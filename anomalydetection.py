from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, extract, func, cast, distinct
from sqlalchemy.types import Float
from typing import List, Optional
from pydantic import BaseModel
from collections import defaultdict

from database import get_db
from models import Vendor, InventoryCase1, OrderCase1

router = APIRouter()

class AnomalyReportItem(BaseModel):
    vendor_id: int
    vendor_name: str
    item_name: str
    month: str
    average_price: float
    anomaly: Optional[str] = None

@router.get("/price-anomaly", response_model=List[AnomalyReportItem], tags=["8-Anomaly Detection"])
async def detect_price_anomalies(
    business_owner_id: int = Query(..., description="Filter anomalies for this business owner"),
    db: AsyncSession = Depends(get_db)
):
    # Step 1: Get vendor IDs linked to this business owner
    vendor_stmt = (
        select(distinct(OrderCase1.vendor_id))
        .where(OrderCase1.business_owner_id == business_owner_id)
    )
    vendor_result = await db.execute(vendor_stmt)
    vendor_ids = [v[0] for v in vendor_result.fetchall()]

    if not vendor_ids:
        return []

    # Step 2: Extract numeric part of price_per_unit
    numeric_price = cast(func.regexp_replace(InventoryCase1.price_per_unit, '[^0-9.]', '', 'g'), Float)

    # Step 3: Get overall average price per item (all vendors)
    overall_stmt = (
        select(
            InventoryCase1.name.label("item_name"),
            func.avg(numeric_price).label("overall_avg_price")
        )
        .group_by(InventoryCase1.name)
    )
    overall_result = await db.execute(overall_stmt)
    overall_avg_map = {row.item_name: float(row.overall_avg_price) for row in overall_result.all()}

    # Step 4: Get vendor-wise monthly average for selected business owner's vendors
    stmt = (
        select(
            InventoryCase1.vendor_id,
            Vendor.name.label("vendor_name"),
            InventoryCase1.name.label("item_name"),
            extract('month', InventoryCase1.created_at).label("month"),
            extract('year', InventoryCase1.created_at).label("year"),
            func.avg(numeric_price).label("avg_price")
        )
        .join(Vendor, Vendor.id == InventoryCase1.vendor_id)
        .where(InventoryCase1.vendor_id.in_(vendor_ids))
        .group_by(
            InventoryCase1.vendor_id, Vendor.name, InventoryCase1.name,
            extract('year', InventoryCase1.created_at),
            extract('month', InventoryCase1.created_at)
        )
        .order_by(
            InventoryCase1.vendor_id, InventoryCase1.name,
            extract('year', InventoryCase1.created_at),
            extract('month', InventoryCase1.created_at)
        )
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Step 5: Generate report and apply anomaly logic
    reports = []
    for row in rows:
        avg_price = float(row.avg_price)
        overall_avg = overall_avg_map.get(row.item_name, avg_price)
        anomaly = None

        if avg_price > overall_avg * 1.2:
            anomaly = "Above historical average"
        elif avg_price < overall_avg * 0.8:
            anomaly = "Below historical average"
        else:
            anomaly = "No anomaly"

        reports.append(AnomalyReportItem(
            vendor_id=row.vendor_id,
            vendor_name=row.vendor_name,
            item_name=row.item_name,
            month=f"{int(row.year)}-{int(row.month):02d}",
            average_price=round(avg_price, 2),
            anomaly=anomaly
        ))

    return reports
