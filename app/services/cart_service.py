"""
Cart Service
Enforces shopping cart business rules, stock availability checks, and item calculations.
"""

from typing import List
from sqlalchemy.orm import Session
from app.models.cart import Cart
from app.schemas.cart import CartResponse, CartItemResponse, CartItemAdd, CartItemUpdate
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.core.exceptions import EntityNotFoundException, BadRequestException, InsufficientStockException


class CartService:
    def __init__(self, db: Session):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)

    def _build_cart_response(self, cart: Cart) -> CartResponse:
        item_responses: List[CartItemResponse] = []
        total_items = 0
        total_amount = 0.0

        for item in cart.items:
            product = item.product
            subtotal = round(product.price * item.quantity, 2)
            total_items += item.quantity
            total_amount += subtotal

            item_responses.append(
                CartItemResponse(
                    id=item.id,
                    product_id=product.id,
                    product_title=product.title,
                    product_sku=product.sku,
                    unit_price=product.price,
                    quantity=item.quantity,
                    subtotal=subtotal,
                    available_stock=product.stock_quantity
                )
            )

        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=item_responses,
            total_items=total_items,
            total_amount=round(total_amount, 2),
            updated_at=cart.updated_at
        )

    def get_user_cart(self, user_id: int) -> CartResponse:
        cart = self.cart_repo.get_or_create(user_id)
        return self._build_cart_response(cart)

    def add_to_cart(self, user_id: int, data: CartItemAdd) -> CartResponse:
        if data.quantity <= 0:
            raise BadRequestException("Quantity must be greater than zero.")

        product = self.product_repo.get_by_id(data.product_id)
        if not product:
            raise EntityNotFoundException("Product", data.product_id)
        if not product.is_active:
            raise BadRequestException(f"Product '{product.title}' is currently unavailable for purchase.")

        cart = self.cart_repo.get_or_create(user_id)
        existing_item = self.cart_repo.get_item(cart.id, product.id)
        current_in_cart = existing_item.quantity if existing_item else 0
        desired_total = current_in_cart + data.quantity

        # Business Rule: Cannot add more than current stock quantity
        if desired_total > product.stock_quantity:
            raise InsufficientStockException(
                product_title=product.title,
                available_stock=product.stock_quantity,
                requested_quantity=desired_total
            )

        self.cart_repo.add_or_update_item(cart.id, product.id, data.quantity)
        self.db.refresh(cart)
        return self._build_cart_response(cart)

    def update_cart_item(self, user_id: int, product_id: int, data: CartItemUpdate) -> CartResponse:
        cart = self.cart_repo.get_or_create(user_id)
        existing_item = self.cart_repo.get_item(cart.id, product_id)
        if not existing_item:
            raise EntityNotFoundException("Cart item for product", product_id)

        if data.quantity == 0:
            self.cart_repo.remove_item(cart.id, product_id)
        else:
            product = self.product_repo.get_by_id(product_id)
            if not product:
                raise EntityNotFoundException("Product", product_id)

            if data.quantity > product.stock_quantity:
                raise InsufficientStockException(
                    product_title=product.title,
                    available_stock=product.stock_quantity,
                    requested_quantity=data.quantity
                )

            self.cart_repo.set_item_quantity(cart.id, product_id, data.quantity)

        self.db.refresh(cart)
        return self._build_cart_response(cart)

    def remove_cart_item(self, user_id: int, product_id: int) -> CartResponse:
        cart = self.cart_repo.get_or_create(user_id)
        removed = self.cart_repo.remove_item(cart.id, product_id)
        if not removed:
            raise EntityNotFoundException("Cart item for product", product_id)
        self.db.refresh(cart)
        return self._build_cart_response(cart)

    def clear_cart(self, user_id: int) -> CartResponse:
        cart = self.cart_repo.get_or_create(user_id)
        self.cart_repo.clear(cart.id)
        self.db.refresh(cart)
        return self._build_cart_response(cart)
