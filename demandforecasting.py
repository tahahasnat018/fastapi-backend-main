from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from typing import List
from pydantic import BaseModel
from database import get_db
from models import InventoryCase1, OrderCase1InventoryMapping, OrderCase1

router = APIRouter()

class DemandForecastItem(BaseModel):
    ingredient_name: str
    avg_monthly_usage: float
    predicted_demand: float
    change_percentage: float

@router.get("/demand-forecast", response_model=List[DemandForecastItem], tags=["5-Demand Forecast"])
async def demand_forecast(business_owner_id: int, db: AsyncSession = Depends(get_db)):
    # Step 1: Aggregate monthly ingredient usage
    stmt = (
        select(
            InventoryCase1.name.label("ingredient_name"),
            extract('month', OrderCase1.created_at).label("month"),
            func.sum(OrderCase1InventoryMapping.quantity).label("monthly_usage"),
            InventoryCase1.id.label("ingredient_id")
        )
        .join(OrderCase1InventoryMapping.inventory)
        .join(OrderCase1InventoryMapping.order)
        .where(OrderCase1.business_owner_id == business_owner_id)
        .group_by(InventoryCase1.name, "month", InventoryCase1.id)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    # Step 2: Organize data by ingredient
    usage_map = {}
    for row in rows:
        usage_map.setdefault(row.ingredient_id, {
            "name": row.ingredient_name,
            "usages": []
        })["usages"].append(row.monthly_usage)

    # Step 3: Apply rule-based forecasting logic
    forecast_data = []
    for ing_id, data in usage_map.items():
        usages = data["usages"]
        name = data["name"]
        num_points = len(usages)
        avg_usage = sum(usages) / max(num_points, 1)

        # Rule-based demand prediction
        if num_points < 100:
            if avg_usage < 5:
                predicted = avg_usage + 2  # buffer
            elif avg_usage < 10:
                predicted = avg_usage * 1.5
            elif avg_usage < 25:
                predicted = avg_usage * 1.3
            elif avg_usage < 50:
                predicted = avg_usage * 1.15
            elif avg_usage < 100:
                predicted = avg_usage * 1.05
            else:
                predicted = avg_usage
        else:
            # Reserved for ML model when more data is available
            # Example placeholder
            # predicted = your_ml_model.predict([...])
            predicted = avg_usage

        # Step 4: Change % Calculation
        change_pct = ((predicted - avg_usage) / avg_usage * 100) if avg_usage != 0 else 0.0

        forecast_data.append(DemandForecastItem(
            ingredient_name=name,
            avg_monthly_usage=round(avg_usage, 2),
            predicted_demand=round(predicted, 2),
            change_percentage=round(change_pct, 2)
        ))

    return forecast_data
