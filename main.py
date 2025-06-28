from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine, AsyncSessionLocal
from models import Base
import crud
import schemas  # Make sure this line exists]
from fastapi import FastAPI
from fastapi import FastAPI
from orderbacklog import router as orderbacklog_router
from orderanalytics import router as order_analytics_router
from fastapi import Query
from fastapi import FastAPI
import orderfulfillment 
from orderhistory import router as orders_router
# make sure this file is in the same directory as main.py
from fastapi import FastAPI
from stockwastage import get_stock_loss  
from stockprediction import router as stock_prediction_router
from stockwastage import router as stockloss_router
from anomalydetection import router as anomaly_router
from supplier_performance import router as supplier_performance
# Adjust the import path based on your project structure
from qualityvendor import router as quality_router
from demandforecasting import router as demand_router
from costconsumption import router as cost_consumption
app = FastAPI()

app.include_router(cost_consumption)

app.include_router(demand_router)

app.include_router(quality_router)

app.include_router(supplier_performance)

app.include_router(anomaly_router)


app.include_router(stock_prediction_router)


app.include_router(stockloss_router)
# Register the router from orderfulfillment
app.include_router(orderfulfillment.router)

app.include_router(orders_router)

app.include_router(order_analytics_router, prefix="/api")

app.include_router(orderbacklog_router)

# Create tables
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.post("/roles/", response_model=schemas.SMEmployeeRoleTypeOut)
async def create_role(role: schemas.SMEmployeeRoleTypeCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_role_type(db, role)

@app.get("/roles/", response_model=list[schemas.SMEmployeeRoleTypeOut])
async def read_roles(
    business_owner_id: int = Query(..., description="ID of the business owner"),
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_all_roles(db, business_owner_id)
@app.get("/roles/{role_id}", response_model=schemas.SMEmployeeRoleTypeOut)
async def read_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await crud.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@app.put("/roles/{role_id}", response_model=schemas.SMEmployeeRoleTypeOut)
async def update_role(role_id: int, role: schemas.SMEmployeeRoleTypeUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.update_role(db, role_id, role)
    if not updated:
        raise HTTPException(status_code=404, detail="Role not found")
    return updated

@app.delete("/roles/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_role(db, role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Deleted successfully"}
