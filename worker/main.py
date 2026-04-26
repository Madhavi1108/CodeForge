import json
import os
import time
import structlog
from confluent_kafka import Consumer, Producer
from sandbox import execute_code, SandboxExecutionError, TimeoutError, LANGUAGE_CONFIG, client as docker_client
from database import get_db_connection

logger = structlog.get_logger()

KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MAX_RETRIES = 3

consumer_conf = {
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'execution_workers',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}

producer_conf = {
    'bootstrap.servers': KAFKA_BROKER,
    'client.id': 'worker-producer'
}

consumer = Consumer(consumer_conf)
producer = Producer(producer_conf)

consumer.subscribe(['code_jobs'])

def publish_to_dlq(payload, error_type, error_msg):
    dlq_payload = {
        "job_id": dict.get(payload, "job_id", ""),
        "user_id": dict.get(payload, "user_id", ""),
        "failure_type": error_type,
        "error_message": error_msg,
        "original_payload": payload
    }
    producer.produce("dead_letter_queue", key=dlq_payload["job_id"], value=json.dumps(dlq_payload))
    producer.flush()

def update_job_status(job_id, status, user_id=None, retry_count=0):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE jobs SET status = %s, retry_count = %s, updated_at = now()
                WHERE id = %s
            """, (status, retry_count, job_id))
        conn.commit()

def save_result(job_id, user_id, stdout, stderr, exit_code, failure_type, error_msg, exec_time):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO results (job_id, stdout, stderr, exit_code, failure_type, error_message, execution_time_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_id) DO UPDATE SET
                    stdout=EXCLUDED.stdout, stderr=EXCLUDED.stderr, exit_code=EXCLUDED.exit_code,
                    failure_type=EXCLUDED.failure_type, error_message=EXCLUDED.error_message,
                    execution_time_ms=EXCLUDED.execution_time_ms
                """, (job_id, stdout, stderr, exit_code, failure_type, error_msg, exec_time))

                # Deduct credits — safe even if the user has no credits row (0 rows updated)
                cur.execute("""
                    UPDATE credits SET balance = GREATEST(balance - 1.0, 0)
                    WHERE user_id = %s
                """, (user_id,))

                final_status = 'COMPLETED' if failure_type is None else 'FAILED'
                cur.execute("""
                    UPDATE jobs SET status = %s, updated_at = now()
                    WHERE id = %s
                """, (final_status, job_id))

            conn.commit()
    except Exception as e:
        logger.error("save_result failed — forcing job to FAILED", job_id=job_id, error=str(e))
        # Last-resort: at least mark the job terminal so it doesn't hang forever
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jobs SET status = 'FAILED', updated_at = now() WHERE id = %s
                    """, (job_id,))
                conn.commit()
        except Exception as e2:
            logger.error("Could not force-fail job", job_id=job_id, error=str(e2))

def process_message(msg):
    try:
        payload = json.loads(msg.value().decode('utf-8'))
    except Exception as e:
        logger.error("Failed to decode message", error=str(e))
        return

    job_id = payload.get("job_id")
    language = payload.get("language")
    code = payload.get("code")
    user_id = payload.get("user_id")
    retry_count = payload.get("retry_count", 0)

    logger.info("Processing job", job_id=job_id, language=language)

    update_job_status(job_id, "RUNNING", retry_count=retry_count)

    stdout, stderr, exit_code, failure_type, error_msg, exec_time = "", "", 0, None, "", 0.0

    try:
        # Timeouts are SYSTEM errors, process crashing USER error, docker API fails SYSTEM error
        stdout, stderr, exit_code, exec_time = execute_code(language, code)
        if exit_code != 0:
            failure_type = "USER_ERROR"
            error_msg = f"Process exited with code {exit_code}"
    except TimeoutError as e:
        failure_type = "TIMEOUT"
        error_msg = str(e)
    except SandboxExecutionError as e:
        failure_type = "SYSTEM_ERROR"
        error_msg = str(e)
    except Exception as e:
        failure_type = "SYSTEM_ERROR"
        error_msg = str(e)
        logger.error("Uncaught execution error", error=str(e), job_id=job_id)

    if failure_type == "SYSTEM_ERROR" and retry_count < MAX_RETRIES:
        logger.warn("Job failed with system error, retrying", job_id=job_id, retries=retry_count)
        payload["retry_count"] = retry_count + 1
        producer.produce("code_jobs", key=user_id, value=json.dumps(payload))
        producer.flush()
        update_job_status(job_id, "PENDING", retry_count=payload["retry_count"])
    else:
        if failure_type == "SYSTEM_ERROR":
            publish_to_dlq(payload, failure_type, error_msg)
            
        # Save result, charge credits, mark as complete or failed
        logger.info("Job execution finished", job_id=job_id, failure_type=failure_type)
        save_result(job_id, user_id, stdout, stderr, exit_code, failure_type, error_msg, int(exec_time))

def fail_stale_pending_jobs():
    """Mark any PENDING jobs older than 2 minutes as FAILED.
    These are jobs whose Kafka messages were consumed by a crashed worker instance
    that never wrote a final result back to the DB.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH stale AS (
                        UPDATE jobs
                        SET status = 'FAILED', updated_at = now()
                        WHERE status IN ('PENDING', 'RUNNING')
                          AND updated_at < now() - INTERVAL '2 minutes'
                        RETURNING id
                    )
                    INSERT INTO results (job_id, failure_type, error_message, execution_time_ms)
                    SELECT id, 'SYSTEM_ERROR', 'Worker restarted — job was lost in transit', 0
                    FROM stale
                    ON CONFLICT (job_id) DO NOTHING
                """)
                affected = cur.rowcount
            conn.commit()
        if affected:
            logger.warning("Cleaned up stale jobs", count=affected)
        else:
            logger.info("No stale jobs found")
    except Exception as e:
        logger.error("Failed to clean stale jobs", error=str(e))

def main():
    logger.info("Worker started, polling code_jobs")

    # Fail any jobs left PENDING/RUNNING by a previously crashed worker
    fail_stale_pending_jobs()

    # Warm up sandbox runtime images on the host daemon to avoid first-run latency
    # (and to fail fast if the daemon can't pull).
    for lang, cfg in LANGUAGE_CONFIG.items():
        image = cfg.get("image")
        if not image:
            continue
        try:
            docker_client.images.get(image)
            logger.info("Sandbox image present", language=lang, image=image)
        except Exception:
            try:
                logger.info("Pulling sandbox image", language=lang, image=image)
                docker_client.images.pull(image)
                logger.info("Sandbox image pulled", language=lang, image=image)
            except Exception as e:
                logger.warning("Failed to pull sandbox image", language=lang, image=image, error=str(e))
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error", error=msg.error())
                continue

            process_message(msg)
            consumer.commit(msg)
            
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
