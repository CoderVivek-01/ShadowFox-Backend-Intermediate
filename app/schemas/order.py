"""
Order Pydantic Schemas
Validates checkout input, status transitions, and response serialization.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    shipping_address: str = Field(..., min_length=5, max_length=500, examples=["452 Tech Boulevard, Suite 10, Silicon Valley, CA 94025"])
    contact_phone: str = Field(..., min_length=7, max_length=20, examples=["+1-555-019-2834"])
    notes: Optional[str] = Field(None, max_length=300, examples=["Leave with building receptionist."])


class OrderStatusUpdate(BaseModel):
    status: OrderStatus = Field(..., description="Target order status", examples=[OrderStatus.CONFIRMED])


class OrderItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    product_title: str
    unit_price: float
    quantity: int
    subtotal: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    status: OrderStatus
    total_amount: float
    shipping_address: str
    contact_phone: str
    notes: Optional[str]
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
