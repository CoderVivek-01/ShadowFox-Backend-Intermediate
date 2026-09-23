"""
Orders Router
Checkout transaction processing, user order history, cancellation, and admin fulfillment.
"""

from typing import Optional
import math
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import api_success, ResponseMetadata
from app.models.user import User
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderStatusUpdate, OrderResponse
from app.services.order_service import OrderService
from app.routers.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/orders", tags=["Orders & Checkout"])


@router.post(
    "/checkout",
    summary="Checkout cart and place order",
    description="Atomically verifies stock for all cart items, deducts warehouse inventory, snapshots pricing, clears the cart, and creates the order.",
    status_code=status.HTTP_201_CREATED
)
def checkout(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    order = service.checkout(current_user.id, data)
    return api_success(
        message="Order placed successfully.",
        data=OrderResponse.model_validate(order).model_dump(),
        status_code=status.HTTP_201_CREATED
    )


@router.get(
    "",
    summary="List authenticated user's orders",
    description="Returns order history for the logged-in customer.",
    status_code=status.HTTP_200_OK
)
def list_my_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    orders, total = service.list_user_orders(current_user.id, page=page, limit=limit)
    data = [OrderResponse.model_validate(o).model_dump() for o in orders]
    meta = ResponseMetadata(
        page=page,
        limit=limit,
        total=total,
        total_pages=math.ceil(total / limit) if total > 0 else 0
    )
    return api_success(
        message="User orders retrieved successfully.",
        data=data,
        meta=meta
    )


@router.get(
    "/admin/all",
    summary="List all orders across all customers (Admin Only)",
    description="Administrative overview with optional status filtering and pagination.",
    status_code=status.HTTP_200_OK
)
def list_all_orders_admin(
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by OrderStatus"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    orders, total = service.list_all_orders(status=status_filter, page=page, limit=limit)
    data = [OrderResponse.model_validate(o).model_dump() for o in orders]
    meta = ResponseMetadata(
        page=page,
        limit=limit,
        total=total,
        total_pages=math.ceil(total / limit) if total > 0 else 0
    )
    return api_success(
        message="All orders retrieved successfully.",
        data=data,
        meta=meta
    )


@router.get(
    "/{order_id}",
    summary="Get order details by ID",
    description="Customers can view their own orders; Admins can view any order.",
    status_code=status.HTTP_200_OK
)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    order = service.get_order_by_id(order_id, current_user.id, current_user.role)
    return api_success(
        message="Order details retrieved.",
        data=OrderResponse.model_validate(order).model_dump()
    )


@router.post(
    "/{order_id}/cancel",
    summary="Cancel order and restock inventory",
    description="Customers can cancel PENDING orders. Admins can cancel orders until delivered. Restores deducted stock to warehouse automatically.",
    status_code=status.HTTP_200_OK
)
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    order = service.cancel_order(order_id, current_user.id, current_user.role)
    return api_success(
        message="Order cancelled successfully and inventory was restocked.",
        data=OrderResponse.model_validate(order).model_dump()
    )


@router.put(
    "/admin/{order_id}/status",
    summary="Update order fulfillment status (Admin Only)",
    description="Updates order lifecycle status (e.g. CONFIRMED, SHIPPED, DELIVERED, CANCELLED). If set to CANCELLED, restocks inventory automatically.",
    status_code=status.HTTP_200_OK
)
def update_order_status_admin(
    order_id: int,
    data: OrderStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    service = OrderService(db)
    order = service.update_order_status(order_id, data)
    return api_success(
        message=f"Order status updated to {order.status.value}.",
        data=OrderResponse.model_validate(order).model_dump()
    )
