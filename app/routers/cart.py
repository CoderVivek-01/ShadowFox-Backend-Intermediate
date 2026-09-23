"""
Cart Router
Shopping cart management endpoints for authenticated customers.
Enforces business rules against adding more items than currently in warehouse stock.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import api_success
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate
from app.services.cart_service import CartService
from app.routers.deps import get_current_user

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


@router.get(
    "",
    summary="Get user's shopping cart",
    description="Returns current items, calculated item subtotals, total cart value, and live warehouse availability.",
    status_code=status.HTTP_200_OK
)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CartService(db)
    cart = service.get_user_cart(current_user.id)
    return api_success(
        message="Shopping cart retrieved.",
        data=cart.model_dump()
    )


@router.post(
    "/items",
    summary="Add product to cart",
    description="Validates product availability. Rejects requests where total desired quantity exceeds current stock.",
    status_code=status.HTTP_200_OK
)
def add_to_cart(
    data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CartService(db)
    cart = service.add_to_cart(current_user.id, data)
    return api_success(
        message="Item added to cart successfully.",
        data=cart.model_dump()
    )


@router.put(
    "/items/{product_id}",
    summary="Update cart item quantity",
    description="Modifies the quantity of a product in the cart. If quantity is set to 0, the item is removed.",
    status_code=status.HTTP_200_OK
)
def update_cart_item(
    product_id: int,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CartService(db)
    cart = service.update_cart_item(current_user.id, product_id, data)
    return api_success(
        message="Cart updated successfully.",
        data=cart.model_dump()
    )


@router.delete(
    "/items/{product_id}",
    summary="Remove product from cart",
    status_code=status.HTTP_200_OK
)
def remove_cart_item(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CartService(db)
    cart = service.remove_cart_item(current_user.id, product_id)
    return api_success(
        message="Item removed from cart.",
        data=cart.model_dump()
    )


@router.delete(
    "",
    summary="Clear entire cart",
    status_code=status.HTTP_200_OK
)
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CartService(db)
    cart = service.clear_cart(current_user.id)
    return api_success(
        message="Cart cleared successfully.",
        data=cart.model_dump()
    )
