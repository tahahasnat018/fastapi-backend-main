from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from typing import List
from pydantic import BaseModel
from database import get_db
from models import InventoryCase1, OrderCase1InventoryMapping, OrderCase1, Wastage
import re

router = APIRouter()

class OptimizedOrderItem(BaseModel):
    ingredient_name: str
    avg_monthly_order: float
    avg_monthly_waste: float
    ai_suggested_order_quantity: float
    cost_savings: float

def extract_price(price_str: str) -> float:
    """Extracts numeric value from a price string like '500 PKR'."""
    if not price_str:
        return 0.0
    match = re.search(r"[\d.]+", price_str)
    return float(match.group()) if match else 0.0

@router.get("/optimized-orders", response_model=List[OptimizedOrderItem], tags=["7-Order Optimization"])
async def get_optimized_orders(business_owner_id: int, db: AsyncSession = Depends(get_db)):
    # Step 1: Avg Monthly Orders
    month = extract('month', OrderCase1.created_at)
    order_stmt = (
        select(
            InventoryCase1.id.label("ingredient_id"),
            InventoryCase1.name.label("ingredient_name"),
            month.label("month"),
            func.sum(OrderCase1InventoryMapping.quantity).label("monthly_order"),
            InventoryCase1.price_per_unit.label("price_str")
        )
        .join(OrderCase1InventoryMapping.inventory)
        .join(OrderCase1InventoryMapping.order)
        .where(OrderCase1.business_owner_id == business_owner_id)
        .group_by(InventoryCase1.id, InventoryCase1.name, month, InventoryCase1.price_per_unit)
    )
    order_result = await db.execute(order_stmt)
    order_rows = order_result.fetchall()

    # Step 2: Avg Monthly Waste
    waste_month = extract('month', Wastage.created_at)
    waste_stmt = (
        select(
            Wastage.ingredient_id,
            waste_month.label("month"),
            func.sum(Wastage.wastage_qty).label("monthly_waste")
        )
        .where(Wastage.business_owner_id == business_owner_id)
        .group_by(Wastage.ingredient_id, waste_month)
    )
    waste_result = await db.execute(waste_stmt)
    waste_rows = waste_result.fetchall()

    # Step 3: Organize Data
    order_map = {}
    for row in order_rows:
        price = extract_price(row.price_str)
        item = order_map.setdefault(row.ingredient_id, {
            "name": row.ingredient_name,
            "orders": [],
            "wastes": [],
            "price": price
        })
        item["orders"].append(row.monthly_order)

    for row in waste_rows:
        if row.ingredient_id in order_map:
            order_map[row.ingredient_id]["wastes"].append(row.monthly_waste)

    # Step 4: Rule-Based + ML Placeholder
    result_data = []
    for ing_id, data in order_map.items():
        orders = data["orders"]
        wastes = data["wastes"]
        price = data["price"]

        avg_order = sum(orders) / max(len(orders), 1)
        avg_waste = sum(wastes) / max(len(wastes), 1) if wastes else 0.0

        waste_reduction_factor = 0.8
        suggested_order = max(avg_order - (waste_reduction_factor * avg_waste), 0)

        # ML Placeholder
        if len(orders) >= 100:
            # predicted_order = your_ml_model.predict(...)
            predicted_order = suggested_order
        else:
            predicted_order = suggested_order

        savings = (avg_order - predicted_order) * price if price else 0.0

        result_data.append(OptimizedOrderItem(
            ingredient_name=data["name"],
            avg_monthly_order=round(avg_order, 2),
            avg_monthly_waste=round(avg_waste, 2),
            ai_suggested_order_quantity=round(predicted_order, 2),
            cost_savings=round(savings, 2)
        ))

    return result_data
