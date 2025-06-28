from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import OrderCase1
from schemas import OrderOut

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/", response_model=list[OrderOut])
async def get_all_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OrderCase1))
    return result.scalars().all()
