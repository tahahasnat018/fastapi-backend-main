from fastapi import APIRouter, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import cast, TIMESTAMP
from datetime import datetime, timedelta
import re

from models import Inventory, MenuIngredient, CustomerOrderMenuMapping, CustomerOrder
from database import get_db  # Make sure it yields AsyncSession

router = APIRouter()

def parse_quantity(quantity_str):
    match = re.match(r"([0-9.]+)([a-zA-Z]*)", quantity_str.strip())
    if not match:
        return 0.0, ""
    value = float(match.group(1))
    unit = match.group(2)
    return value, unit

async def calculate_usage_rate(session: AsyncSession, ingredient_id: int, days_back: int = 30):
    # Get MenuIngredients for this ingredient
    result = await session.execute(
        select(MenuIngredient).filter(MenuIngredient.ingredient_id == ingredient_id)
    )
    menu_ingredients = result.scalars().all()

    if not menu_ingredients:
        return 0.0

    date_threshold = datetime.utcnow() - timedelta(days=days_back)
    total_used_qty = 0.0

    for mi in menu_ingredients:
        mi_qty, _ = parse_quantity(mi.quantity)

        # Count all orders containing this menu item since date_threshold
        result_orders = await session.execute(
            select(CustomerOrderMenuMapping)
            .join(CustomerOrder)
            .filter(
                CustomerOrderMenuMapping.menu_id == mi.menu_id,
                cast(CustomerOrder.delivery_datetime, TIMESTAMP) >= date_threshold,
            )
        )
        orders_count = len(result_orders.scalars().all())

        total_used_qty += mi_qty * orders_count

    average_daily_usage = total_used_qty / days_back
    return average_daily_usage

def predict_depletion_day(current_stock, average_daily_usage):
    if average_daily_usage <= 0:
        return None  # Cannot predict depletion

    days_until_depletion = current_stock / average_daily_usage
    depletion_date = datetime.utcnow() + timedelta(days=days_until_depletion)
    return depletion_date.isoformat()

@router.get("/stock-prediction/all", tags=["4-Stock Prediction"])
async def stock_prediction_all(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Inventory))
    ingredients = result.scalars().all()

    results = []
    for ingredient in ingredients:
        avg_usage = await calculate_usage_rate(db, ingredient.id, days_back=30)
        depletion_date = predict_depletion_day(
            current_stock=ingredient.current_stock or 0,
            average_daily_usage=avg_usage,
        )

        results.append({
            "ingredient_name": ingredient.name,
            "current_stock": ingredient.current_stock,
            "average_daily_usage": avg_usage,
            "predicted_depletion_date": depletion_date,
        })

    return results
