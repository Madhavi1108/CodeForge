import json
import os
import structlog
from confluent_kafka import Consumer, Producer

logger = structlog.get_logger()
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

consumer_conf = {
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'ai_workers',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}

consumer = Consumer(consumer_conf)
consumer.subscribe(['explanation_jobs', 'plagiarism_jobs'])

def explain_code(code: str) -> dict:
    # Mock LLM API Call
    return {
        "explanation": "This code appears to perform standard data structure manipulation.",
        "complexity": "O(N)",
        "improvements": "Consider using meaningful variable names and adding comments to complex logic branches."
    }

def check_plagiarism(code: str) -> dict:
    # Mock Plagiarism heuristics
    similarity_score = 0.15 # 15% similiarity found
    return {
        "similarity_score": similarity_score
    }

def main():
    logger.info("AI Worker started, polling AI topics")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error", error=msg.error())
                continue

            topic = msg.topic()
            try:
                payload = json.loads(msg.value().decode('utf-8'))
                job_id = payload.get("job_id")
                code = payload.get("code")
                user_id = payload.get("user_id")
                
                logger.info("Processing AI job", job_id=job_id, topic=topic)
                
                if topic == "explanation_jobs":
                    result = explain_code(code)
                elif topic == "plagiarism_jobs":
                    result = check_plagiarism(code)
                else:
                    logger.warning("Unknown topic", topic=topic)
                    result = {}
                
                # In a complete implementation, this result is written back to PostgreSQL
                # For brevity of this system architecture, we will simply log it
                logger.info("AI Task completed", job_id=job_id, result=result, topic=topic)
                
                consumer.commit(msg)
            except Exception as e:
                logger.error("Failed to process AI message", error=str(e), topic=topic)
                
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
