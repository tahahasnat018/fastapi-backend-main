from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Vendor, OrderCase1, OrderCase1InventoryMapping, InventoryCase1
from schemas import EnhancedOrderHistoryOut
from datetime import datetime

router = APIRouter()

@router.get(
    "/vendors/analytics",
    response_model=list[EnhancedOrderHistoryOut],
    tags=["Vendor Analytics"]
)
async def get_vendor_order_analytics(
    business_owner_id: int = Query(..., description="Filter orders by business_owner_id"),
    db: AsyncSession = Depends(get_db)
):
    vendors_result = await db.execute(select(Vendor))
    vendor_list = vendors_result.scalars().all()

    results = []

    for vendor in vendor_list:
        # Filter orders by vendor_id and business_owner_id
        orders_result = await db.execute(
            select(OrderCase1).where(
                OrderCase1.vendor_id == vendor.id,
                OrderCase1.business_owner_id == business_owner_id
            )
        )
        orders = orders_result.scalars().all()
        total_orders = len(orders)

        if total_orders == 0:
            continue

        fulfilled_orders = [o for o in orders if o.status_type_id == 5]

        delay_days = []
        for o in fulfilled_orders:
            try:
                updated_at = o.updated_at if isinstance(o.updated_at, datetime) else datetime.fromisoformat(o.updated_at)
                delivery_date = o.delivery_date if isinstance(o.delivery_date, datetime) else datetime.fromisoformat(o.delivery_date)
                delay_days.append((updated_at - delivery_date).days)
            except Exception:
                continue

        average_delay = round(sum(delay_days) / len(delay_days), 2) if delay_days else None
        fulfillment_percentage = round((len(fulfilled_orders) / total_orders) * 100, 2)
        order_accuracy_percentage = fulfillment_percentage

        created_dates = [o.created_at for o in orders if o.created_at]
        first_order_date = min(created_dates) if created_dates else None
        last_order_date = max(created_dates) if created_dates else None

        total_order_value = 0
        for order in orders:
            mapping_result = await db.execute(
                select(OrderCase1InventoryMapping).where(OrderCase1InventoryMapping.order_id == order.id)
            )
            mappings = mapping_result.scalars().all()

            for mapping in mappings:
                inventory = await db.get(InventoryCase1, mapping.inventory_id)
                if inventory and inventory.price_per_unit:
                    # Assuming price_per_unit is numeric (int or float)
                    total_order_value += inventory.price_per_unit * mapping.quantity

        average_order_cost = round(total_order_value / total_orders, 2) if total_orders else None

        results.append(EnhancedOrderHistoryOut(
            vendor_id=vendor.id,
            supplier=vendor.name,
            total_orders=total_orders,
            fulfillment_percentage=fulfillment_percentage,
            on_time_delivery_percentage=None,
            average_delay_days=average_delay,
            average_order_cost=average_order_cost,
            order_accuracy_percentage=order_accuracy_percentage,
            first_order_date=first_order_date,
            last_order_date=last_order_date,
            total_order_value=round(total_order_value, 2)
        ))

    return results
