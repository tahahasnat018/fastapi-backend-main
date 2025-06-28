from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ----------------------------
# SMEmployeeRoleType Schemas
# ----------------------------

class SMEmployeeRoleTypeBase(BaseModel):
    business_owner_id: int
    value: str
    code: Optional[str] = None

class SMEmployeeRoleTypeCreate(SMEmployeeRoleTypeBase):
    pass

class SMEmployeeRoleTypeUpdate(SMEmployeeRoleTypeBase):
    pass

class SMEmployeeRoleTypeOut(SMEmployeeRoleTypeBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

# ----------------------------
# Basic Order Output Schema
# ----------------------------

class OrderOut(BaseModel):
    id: int
    delivery_date: Optional[datetime]
    status_type_id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    business_owner_id: Optional[int]
    comment: Optional[str]
    vendor_id: Optional[int]
    payment_invoice_url: Optional[str]

    class Config:
        orm_mode = True

# ----------------------------
# Order History Schemas
# ----------------------------

class OrderHistoryOut(BaseModel):
    supplier: str
    total_orders: int

# ----------------------------
# Enhanced Order History Metrics
# ----------------------------

class EnhancedOrderHistoryOut(BaseModel):
    vendor_id: int
    supplier: str = Field(..., description="Vendor/Supplier name")
    total_orders: int = Field(..., description="Total number of orders")
    fulfillment_percentage: Optional[float] = Field(None, description="Percentage of orders fulfilled successfully")
    on_time_delivery_percentage: Optional[float] = Field(None, description="Percentage of orders delivered on time")
    average_delay_days: Optional[float] = Field(None, description="Average delay in days for late deliveries")
    average_order_cost: Optional[float] = Field(None, description="Average cost per order")
    order_accuracy_percentage: Optional[float] = Field(None, description="Percentage of accurate orders")
    first_order_date: Optional[datetime] = Field(None, description="Date of first order with this vendor")
    last_order_date: Optional[datetime] = Field(None, description="Date of most recent order")
    total_order_value: Optional[float] = Field(None, description="Total monetary value of all orders")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# ----------------------------
# Order History Summary
# ----------------------------

class OrderHistorySummary(BaseModel):
    total_vendors: int = Field(..., description="Total number of vendors")
    total_orders: int = Field(..., description="Total number of orders across all vendors")
    overall_average_cost: float = Field(..., description="Average order cost across all vendors")
    overall_fulfillment_rate: float = Field(..., description="Overall fulfillment rate percentage")
    total_business_value: float = Field(..., description="Total value of all orders")

    class Config:
        from_attributes = True
