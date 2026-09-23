"""
Products & Inventory Router
Public product catalog search and Admin-restricted inventory control.
"""

from typing import Optional
import math
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import api_success, ResponseMetadata
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    StockAdjustmentRequest
)
from app.services.product_service import ProductService
from app.routers.deps import get_current_admin

router = APIRouter(prefix="/products", tags=["Products & Inventory"])


@router.get(
    "",
    summary="List, search, and filter products",
    description="Public endpoint to browse catalog with keyword search, category filter, price bounds, stock filter, and pagination.",
    status_code=status.HTTP_200_OK
)
def list_products(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search keyword in title, description, or SKU"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock_only: bool = Query(False, description="Filter only products with stock > 0"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    products, total = service.list_products(
        category_id=category_id,
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        page=page,
        limit=limit
    )

    data = [ProductResponse.model_validate(p).model_dump() for p in products]
    meta = ResponseMetadata(
        page=page,
        limit=limit,
        total=total,
        total_pages=math.ceil(total / limit) if total > 0 else 0
    )

    return api_success(
        message="Products retrieved successfully.",
        data=data,
        meta=meta
    )


@router.get(
    "/{product_id}",
    summary="Get single product details by ID",
    status_code=status.HTTP_200_OK
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    service = ProductService(db)
    product = service.get_by_id(product_id)
    return api_success(
        message="Product details retrieved.",
        data=ProductResponse.model_validate(product).model_dump()
    )


@router.post(
    "",
    summary="Create a new product (Admin Only)",
    description="Restricted to store administrators. Automatically logs initial stock in InventoryLog.",
    status_code=status.HTTP_201_CREATED
)
def create_product(
    data: ProductCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    product = service.create_product(data)
    return api_success(
        message="Product created successfully.",
        data=ProductResponse.model_validate(product).model_dump(),
        status_code=status.HTTP_201_CREATED
    )


@router.put(
    "/{product_id}",
    summary="Update product details (Admin Only)",
    status_code=status.HTTP_200_OK
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    product = service.update_product(product_id, data)
    return api_success(
        message="Product updated successfully.",
        data=ProductResponse.model_validate(product).model_dump()
    )


@router.delete(
    "/{product_id}",
    summary="Delete product (Admin Only)",
    status_code=status.HTTP_200_OK
)
def delete_product(
    product_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    service.delete_product(product_id)
    return api_success(message=f"Product with ID {product_id} deleted successfully.")


@router.post(
    "/{product_id}/adjust-stock",
    summary="Adjust product inventory stock (Admin Only)",
    description="Safely restocks or decrements warehouse inventory. Rejects adjustments that result in negative stock. Automatically generates an audit trail entry.",
    status_code=status.HTTP_200_OK
)
def adjust_stock(
    product_id: int,
    data: StockAdjustmentRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    product = service.adjust_stock(product_id, data)
    return api_success(
        message="Inventory stock adjusted successfully.",
        data=ProductResponse.model_validate(product).model_dump()
    )
