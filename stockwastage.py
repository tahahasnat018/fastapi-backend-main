from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import InventoryCase1, Wastage
from pydantic import BaseModel
from typing import List

router = APIRouter()

class StockLossItem(BaseModel):
    ingredient_name: str
    wastage_qty: float
    loss_value: float
    suggestions: str = ""

@router.get(
    "/stock-loss",
    response_model=List[StockLossItem],
    tags=["10-Stock Loss"]
)
async def get_stock_loss(
    business_owner_id: int = Query(..., description="Business Owner ID"),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            InventoryCase1.name,
            Wastage.wastage_qty,
            Wastage.loss_value
        )
        .join(Wastage, InventoryCase1.id == Wastage.ingredient_id)
        .where(Wastage.business_owner_id == business_owner_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        StockLossItem(
            ingredient_name=row.name,
            wastage_qty=row.wastage_qty,
            loss_value=row.loss_value,
            suggestions=""
        )
        for row in rows
    ]
