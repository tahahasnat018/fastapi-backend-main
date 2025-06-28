from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import OrderCase1, StatusType
from pydantic import BaseModel
from typing import List

router = APIRouter()

class OrderFulfillmentSummary(BaseModel):
    status: str
    total_orders: int
    percentage: float

@router.get(
    "/orders/fulfillment-summary",
    response_model=List[OrderFulfillmentSummary],
    tags=["9-Order Fulfillment"]
)
async def get_order_fulfillment_summary(
    business_owner_id: int = Query(..., description="Filter by Business Owner ID"),
    db: AsyncSession = Depends(get_db)
):
    # Total orders for the business owner
    total_orders_result = await db.execute(
        select(func.count()).select_from(OrderCase1).where(OrderCase1.business_owner_id == business_owner_id)
    )
    total_orders = total_orders_result.scalar_one()

    if total_orders == 0:
        return []

    # Grouped count by status_type_id for the business owner
    grouped_result = await db.execute(
        select(OrderCase1.status_type_id, func.count())
        .where(OrderCase1.business_owner_id == business_owner_id)
        .group_by(OrderCase1.status_type_id)
    )
    grouped_data = grouped_result.all()

    # Get status labels
    status_types_result = await db.execute(select(StatusType))
    status_types = {s.id: s.value for s in status_types_result.scalars().all()}

    response = []
    for status_type_id, count in grouped_data:
        label = status_types.get(status_type_id, f"Status {status_type_id}")
        percentage = round((count / total_orders) * 100, 2)
        response.append(OrderFulfillmentSummary(
            status=label,
            total_orders=count,
            percentage=percentage
        ))

    return response
