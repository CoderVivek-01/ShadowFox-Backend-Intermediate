"""
Cart Pydantic Schemas
Validates user cart additions, updates, and serialized cart totals.
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: int = Field(..., gt=0, description="ID of the product to add to cart", examples=[1])
    quantity: int = Field(1, gt=0, description="Quantity to add (must be at least 1)", examples=[2])


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0, description="New quantity (setting to 0 removes the item)", examples=[3])


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_title: str
    product_sku: str
    unit_price: float
    quantity: int
    subtotal: float
    available_stock: int


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_items: int
    total_amount: float
    updated_at: datetime
