"""
Inventory & Admin Analytics Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.inventory_log import InventoryChangeType


class InventoryLogResponse(BaseModel):
    id: int
    product_id: int
    change_type: InventoryChangeType
    quantity_changed: int
    previous_quantity: int
    new_quantity: int
    reference_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminAnalyticsResponse(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_revenue: float
    out_of_stock_products_count: int
    low_stock_products_count: int
