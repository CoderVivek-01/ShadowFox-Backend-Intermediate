"""
Admin Dashboard & Audit Router
Provides operational analytics, inventory audit trail inspection, and user account listing.
"""

from typing import Optional
import math
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import api_success, ResponseMetadata
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.inventory import AdminAnalyticsResponse, InventoryLogResponse
from app.repositories.user_repository import UserRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.inventory_repository import InventoryRepository
from app.routers.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Operations & Analytics"])


@router.get(
    "/analytics",
    summary="Get business and warehouse analytics (Admin Only)",
    description="Summarizes total registered users, products, orders, total realized revenue, out-of-stock count, and low-stock alerts.",
    status_code=status.HTTP_200_OK
)
def get_analytics(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    product_repo = ProductRepository(db)
    order_repo = OrderRepository(db)

    analytics = AdminAnalyticsResponse(
        total_users=user_repo.count(),
        total_products=product_repo.count_total(),
        total_orders=order_repo.count_all(),
        total_revenue=order_repo.get_total_revenue(),
        out_of_stock_products_count=product_repo.count_out_of_stock(),
        low_stock_products_count=product_repo.count_low_stock(threshold=5)
    )

    return api_success(
        message="Analytics metrics computed successfully.",
        data=analytics.model_dump()
    )


@router.get(
    "/inventory-logs",
    summary="Get inventory movement audit logs (Admin Only)",
    description="Inspect audit history for all stock changes (purchases, restocks, cancellations, manual adjustments).",
    status_code=status.HTTP_200_OK
)
def get_inventory_logs(
    product_id: Optional[int] = Query(None, description="Filter logs for a specific product ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    repo = InventoryRepository(db)
    skip = (max(1, page) - 1) * limit
    logs = repo.list_logs(product_id=product_id, skip=skip, limit=limit)
    total = repo.count_logs(product_id=product_id)

    data = [InventoryLogResponse.model_validate(l).model_dump() for l in logs]
    meta = ResponseMetadata(
        page=page,
        limit=limit,
        total=total,
        total_pages=math.ceil(total / limit) if total > 0 else 0
    )

    return api_success(
        message="Inventory audit logs retrieved successfully.",
        data=data,
        meta=meta
    )


@router.get(
    "/users",
    summary="List all users (Admin Only)",
    status_code=status.HTTP_200_OK
)
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    repo = UserRepository(db)
    skip = (max(1, page) - 1) * limit
    users = repo.list_all(skip=skip, limit=limit)
    total = repo.count()

    data = [UserResponse.model_validate(u).model_dump() for u in users]
    meta = ResponseMetadata(
        page=page,
        limit=limit,
        total=total,
        total_pages=math.ceil(total / limit) if total > 0 else 0
    )

    return api_success(
        message="Users list retrieved successfully.",
        data=data,
        meta=meta
    )
