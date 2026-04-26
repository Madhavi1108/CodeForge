import hashlib
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from redis.asyncio import Redis

from models import User, Job, Result
from schemas import JobSubmit, JobResponse, JobStatusResponse
from core.database import get_db
from core.security import get_current_user
from core.redis_client import get_redis
from core.kafka_producer import kafka_producer
from core.observability import jobs_enqueued_total, logger
from core.config import settings

router = APIRouter()

async def check_rate_limit(redis: Redis, user_id: str):
    # Rate limit: max requests per minute
    key = f"rate_limit:{user_id}"
    req_count = await redis.incr(key)
    if req_count == 1:
        await redis.expire(key, 60)
    
    if req_count > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

@router.post("/", response_model=JobResponse)
async def submit_job(job_in: JobSubmit, 
                    current_user: User = Depends(get_current_user), 
                    db: AsyncSession = Depends(get_db),
                    redis: Redis = Depends(get_redis)):
    
    # 1. Rate limiting
    await check_rate_limit(redis, str(current_user.id))

    # 2. Hash code for caching/idempotency
    code_hash = hashlib.sha256(f"{job_in.language}:{job_in.code}".encode()).hexdigest()
    
    # 3. Check Idempotency via DB
    query = select(Job).where(Job.user_id == current_user.id, Job.idempotency_key == job_in.idempotency_key)
    existing_job = (await db.execute(query)).scalars().first()
    if existing_job:
        logger.info("Idempotency hit", user_id=str(current_user.id), idempotency_key=job_in.idempotency_key)
        return existing_job

    # 4. Save Job to DB
    new_job = Job(
        user_id=current_user.id,
        idempotency_key=job_in.idempotency_key,
        language=job_in.language,
        code_hash=code_hash,
        status="PENDING",
        priority=job_in.priority
    )
    db.add(new_job)
    try:
        await db.commit()
        await db.refresh(new_job)
    except IntegrityError:
        await db.rollback()
        # Edge case: race condition on idempotency insert
        existing_job = (await db.execute(query)).scalars().first()
        return existing_job

    # 5. Publish to Kafka
    topic = "code_jobs"
    payload = {
        "job_id": str(new_job.id),
        "user_id": str(current_user.id),
        "language": job_in.language,
        "code": job_in.code,
        "priority": job_in.priority
    }
    
    # Partition by user_id to ensure ordering per tenant
    kafka_producer.produce(topic=topic, key=str(current_user.id), value=payload)
    
    jobs_enqueued_total.labels(language=job_in.language, priority=str(job_in.priority)).inc()
    
    logger.info("Job submitted", job_id=str(new_job.id), user_id=str(current_user.id))
    
    return new_job

@router.get("/failed", response_model=list[JobStatusResponse])
async def get_failed_jobs(current_user: User = Depends(get_current_user), 
                         db: AsyncSession = Depends(get_db)):
    query = select(Job).options(selectinload(Job.result)).where(Job.user_id == current_user.id, Job.status == "FAILED")
    jobs = (await db.execute(query)).scalars().all()
    return jobs

@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, 
                        current_user: User = Depends(get_current_user), 
                        db: AsyncSession = Depends(get_db)):
    query = select(Job).options(selectinload(Job.result)).where(Job.id == job_id, Job.user_id == current_user.id)
    job = (await db.execute(query)).scalars().first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
