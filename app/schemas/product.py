"""
Product and Inventory Schemas
Validates catalog input, price bounds, inventory adjustments, and output serialization.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ProductBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150, examples=["Logitech MX Master 3S"])
    sku: str = Field(..., min_length=3, max_length=50, examples=["LOGI-MXM3S-BLK"])
    description: Optional[str] = Field(None, max_length=2000, examples=["Ergonomic wireless mouse with 8K DPI tracking."])
    price: float = Field(..., gt=0, description="Product price must be greater than zero", examples=[99.99])
    stock_quantity: int = Field(..., ge=0, description="Initial inventory stock count", examples=[50])
    category_id: int = Field(..., gt=0, description="ID of the associated category", examples=[1])


class ProductCreate(ProductBase):
    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, v: float) -> float:
        return round(v, 2)


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None

    @field_validator("price")
    @classmethod
    def validate_price_precision(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            return round(v, 2)
        return v


class StockAdjustmentRequest(BaseModel):
    adjustment: int = Field(..., description="Quantity to add (positive) or deduct (negative)", examples=[15])
    reason: str = Field(..., min_length=3, max_length=255, examples=["Warehouse shipment arrival batch #402"])

    @field_validator("adjustment")
    @classmethod
    def validate_non_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Adjustment value cannot be zero.")
        return v


class CategoryBrief(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: int
    title: str
    slug: str
    sku: str
    description: Optional[str]
    price: float
    stock_quantity: int
    is_active: bool
    category_id: int
    category: Optional[CategoryBrief] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
