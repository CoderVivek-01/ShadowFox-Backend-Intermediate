"""
Category Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80, examples=["Electronics"])
    description: Optional[str] = Field(None, max_length=500, examples=["Devices, gadgets, and computing accessories"])


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=80)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: int
    slug: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
