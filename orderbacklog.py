from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pydantic import BaseModel

from models import OrderCase1, InventoryCase1, Vendor, OrderCase1InventoryMapping
from database import get_db

router = APIRouter()

class OrderBacklogItem(BaseModel):
    order_id: int
    item_names: List[str]
    supplier_name: str
    order_date: str
    delivery_date: str
    delayed: bool
    reason_of_delay: Optional[str] = None

@router.get("/order-backlog", response_model=List[OrderBacklogItem], tags=["2-order_backlog"])
async def get_order_backlog(
    business_owner_id: int = Query(..., description="Filter by Business Owner ID"),
    db: AsyncSession = Depends(get_db)
):
    delay_threshold = timedelta(days=100)
    today = datetime.utcnow()

    stmt = (
        select(OrderCase1, OrderCase1InventoryMapping, InventoryCase1, Vendor)
        .join(OrderCase1InventoryMapping, OrderCase1.id == OrderCase1InventoryMapping.order_id)
        .join(InventoryCase1, InventoryCase1.id == OrderCase1InventoryMapping.inventory_id)
        .join(Vendor, Vendor.id == OrderCase1.vendor_id)
        .where(OrderCase1.business_owner_id == business_owner_id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    order_map: Dict[int, OrderBacklogItem] = {}

    for order, mapping, inventory, vendor in rows:
        delivery_date_raw = order.delivery_date
        delayed = False
        reason_of_delay = None

        if delivery_date_raw:
            try:
                delivery_date = (
                    datetime.fromisoformat(delivery_date_raw)
                    if isinstance(delivery_date_raw, str)
                    else delivery_date_raw
                )
                if today - delivery_date > delay_threshold:
                    delayed = True
                    reason_of_delay = order.comment or None
            except Exception:
                delivery_date = delivery_date_raw
        else:
            delivery_date = None

        order_date_raw = order.updated_at or order.created_at or datetime.utcnow()
        order_date_str = order_date_raw.strftime("%d %b %Y") if isinstance(order_date_raw, datetime) else str(order_date_raw)
        delivery_date_str = delivery_date.strftime("%d %b %Y") if isinstance(delivery_date, datetime) else str(delivery_date or "")

        if order.id not in order_map:
            order_map[order.id] = OrderBacklogItem(
                order_id=order.id,
                item_names=[],
                supplier_name=vendor.name,
                order_date=order_date_str,
                delivery_date=delivery_date_str,
                delayed=delayed,
                reason_of_delay=reason_of_delay if delayed else None
            )

        order_map[order.id].item_names.append(inventory.name)

    return list(order_map.values())
