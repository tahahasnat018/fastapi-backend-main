from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, cast
from sqlalchemy.dialects.postgresql import INTERVAL
from typing import List
from pydantic import BaseModel

from database import get_db
from models import Vendor, OrderCase1

router = APIRouter()

class SupplierPerformanceItem(BaseModel):
    supplier_name: str
    order_fulfillment_prediction: str
    delivery_accuracy: str
    risk_level: str
    suggested_action: str

@router.get(
    "/supplier-performance",
    response_model=List[SupplierPerformanceItem],
    tags=["3-Supplier Performance"]
)
async def get_supplier_performance(
    business_owner_id: int = Query(..., description="Filter by business owner ID"),
    db: AsyncSession = Depends(get_db)
):
    # Subquery: Average delivery time per vendor for this business owner
    avg_delivery_subq = (
        select(
            OrderCase1.vendor_id,
            func.avg(
                cast(OrderCase1.updated_at - func.to_timestamp(OrderCase1.delivery_date, 'YYYY-MM-DD HH24:MI:SS'), INTERVAL)
            ).label("avg_delivery_time")
        )
        .where(
            OrderCase1.status_type_id == 5,
            OrderCase1.business_owner_id == business_owner_id
        )
        .group_by(OrderCase1.vendor_id)
        .subquery()
    )

    # Main query with filter
    stmt = (
        select(
            Vendor.name.label("supplier_name"),
            func.count(OrderCase1.id).label("total_orders"),
            func.count(
                func.nullif(OrderCase1.status_type_id != 5, True)
            ).label("fulfilled_orders"),
            func.count(
                case(
                    (
                        (OrderCase1.status_type_id == 5) &
                        ((OrderCase1.updated_at - func.to_timestamp(OrderCase1.delivery_date, 'YYYY-MM-DD HH24:MI:SS')) <= avg_delivery_subq.c.avg_delivery_time),
                        1
                    )
                )
            ).label("on_time_deliveries")
        )
        .join(Vendor, Vendor.id == OrderCase1.vendor_id)
        .join(avg_delivery_subq, avg_delivery_subq.c.vendor_id == Vendor.id)
        .where(OrderCase1.business_owner_id == business_owner_id)
        .group_by(Vendor.name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    data = []
    for row in rows:
        total = row.total_orders or 1
        fulfilled = row.fulfilled_orders or 0
        on_time = row.on_time_deliveries or 0

        fulfillment_rate = round((fulfilled / total) * 100)
        delivery_accuracy = round((on_time / total) * 100)

        if fulfillment_rate >= 90:
            risk = "Low"
            action = "Continue Ordering"
        elif fulfillment_rate >= 70:
            risk = "Medium"
            action = "Monitor Performance"
        else:
            risk = "High"
            action = "Reconsider Supplier"

        data.append(SupplierPerformanceItem(
            supplier_name=row.supplier_name,
            order_fulfillment_prediction=f"{fulfillment_rate}%",
            delivery_accuracy=f"{delivery_accuracy}%",
            risk_level=risk,
            suggested_action=action
        ))

    return data
