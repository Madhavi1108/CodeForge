from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID4
    email: EmailStr
    role: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class JobSubmit(BaseModel):
    idempotency_key: str
    language: str = Field(..., description="python, cpp, java")
    code: str
    priority: int = 0

class JobResponse(BaseModel):
    id: UUID4
    status: str
    
    class Config:
        from_attributes = True

class ResultResponse(BaseModel):
    stdout: Optional[str]
    stderr: Optional[str]
    exit_code: Optional[int]
    failure_type: Optional[str]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    
    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    id: UUID4
    status: str
    result: Optional[ResultResponse]
    
    class Config:
        from_attributes = True

class ExplanationRequest(BaseModel):
    code: str

class ExplanationResponse(BaseModel):
    explanation: str
    complexity: str
    improvements: str

class PlagiarismRequest(BaseModel):
    code: str

class PlagiarismResponse(BaseModel):
    similarity_score: float
