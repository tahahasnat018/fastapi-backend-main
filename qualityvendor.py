from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, text
from sqlalchemy.types import DateTime
from typing import List
from pydantic import BaseModel

from database import get_db
from models import Vendor, OrderCase1

router = APIRouter()

class VendorQualityItem(BaseModel):
    vendor_name: str
    avg_delivery_time_days: float
    quality_score: float
    order_accuracy: float

@router.get("/vendor-quality", response_model=List[VendorQualityItem], tags=["6-Vendor Quality"])
async def get_vendor_quality(
    business_owner_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # Cast delivery_date (string) to DateTime
    delivery_date_cast = cast(text("delivery_date"), DateTime)

    stmt = (
        select(
            Vendor.name.label("vendor_name"),
            func.avg(
                func.greatest(
                    func.date_part('day', cast(OrderCase1.updated_at, DateTime) - delivery_date_cast)
                
                )
            ).label("avg_delivery_time"),
            func.count(OrderCase1.id).label("total_orders"),
            func.count(
                func.nullif(OrderCase1.status_type_id != 5, True)
            ).label("fulfilled_orders")
        )
        .join(Vendor, Vendor.id == OrderCase1.vendor_id)
        .where(OrderCase1.business_owner_id == business_owner_id)
        .group_by(Vendor.name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    vendor_data = []
    for row in rows:
        total_orders = row.total_orders or 1
        fulfilled_orders = row.fulfilled_orders or 0
        accuracy = round((fulfilled_orders / total_orders) * 100, 2)

        if accuracy >= 90:
            score = 5.0
        elif accuracy >= 75:
            score = 4.0
        elif accuracy >= 60:
            score = 3.0
        elif accuracy >= 45:
            score = 2.0
        else:
            score = 1.0

        vendor_data.append(VendorQualityItem(
            vendor_name=row.vendor_name,
            avg_delivery_time_days=round(row.avg_delivery_time or 0, 2),
            quality_score=score,
            order_accuracy=accuracy
        ))

    return vendor_data
