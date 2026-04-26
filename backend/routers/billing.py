from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import User, Credit
from core.database import get_db
from core.security import get_current_user

router = APIRouter()

class TopupRequest(BaseModel):
    amount: float

class CreditResponse(BaseModel):
    balance: float

@router.get("/", response_model=CreditResponse)
async def get_credits(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Credit).where(Credit.user_id == current_user.id)
    credit = (await db.execute(query)).scalars().first()
    if not credit:
        raise HTTPException(status_code=404, detail="Credit profile not found")
    return {"balance": credit.balance}

@router.post("/topup", response_model=CreditResponse)
async def topup_credits(request: TopupRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
        
    query = select(Credit).where(Credit.user_id == current_user.id)
    credit = (await db.execute(query)).scalars().first()
    
    if not credit:
        credit = Credit(user_id=current_user.id, balance=request.amount)
        db.add(credit)
    else:
        credit.balance += request.amount
        
    await db.commit()
    await db.refresh(credit)
    return {"balance": credit.balance}
