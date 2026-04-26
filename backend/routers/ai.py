import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from schemas import ExplanationRequest, ExplanationResponse, PlagiarismRequest, PlagiarismResponse
from core.database import get_db
from core.security import get_current_user
from core.kafka_producer import kafka_producer

router = APIRouter()

@router.post("/explain")
async def explain_code(request: ExplanationRequest, current_user: User = Depends(get_current_user)):
    # In a full edge setup, we'd wait for a websocket or return a job ID.
    # For now, we will publish the explanation job. The AI worker will process it.
    job_id = str(uuid.uuid4())
    
    payload = {
        "job_id": job_id,
        "user_id": str(current_user.id),
        "code": request.code,
        "task": "explanation"
    }
    kafka_producer.produce("explanation_jobs", key=str(current_user.id), value=payload)
    
    return {"message": "Explanation job queued", "job_id": job_id}

@router.post("/plagiarism")
async def check_plagiarism(request: PlagiarismRequest, current_user: User = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    
    payload = {
        "job_id": job_id,
        "user_id": str(current_user.id),
        "code": request.code,
        "task": "plagiarism"
    }
    kafka_producer.produce("plagiarism_jobs", key=str(current_user.id), value=payload)
    
    return {"message": "Plagiarism check queued", "job_id": job_id}
