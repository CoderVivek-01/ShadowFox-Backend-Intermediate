"""
Order Service
Transactional checkout flow, atomic inventory deductions, status management, and restock upon cancellation.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.order import Order, OrderStatus
from app.models.inventory_log import InventoryChangeType
from app.models.user import UserRole
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.repositories.order_repository import OrderRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.inventory_repository import InventoryRepository
from app.core.exceptions import (
    EntityNotFoundException,
    BadRequestException,
    InsufficientStockException,
    ForbiddenException
)


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)
        self.inventory_repo = InventoryRepository(db)

    def _generate_order_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"ORD-{date_str}-{random_suffix}"

    def checkout(self, user_id: int, data: OrderCreate) -> Order:
        """
        Executes an atomic checkout transaction:
        1. Validates that the cart is not empty.
        2. Validates that every product has sufficient stock.
        3. Deducts stock from each product atomically.
        4. Writes audit records to InventoryLog.
        5. Creates the Order and snapshots OrderItems with unit prices.
        6. Clears the user's cart.
        7. Commits the transaction or rolls back on any failure.
        """
        cart = self.cart_repo.get_by_user_id(user_id)
        if not cart or not cart.items:
            raise BadRequestException("Your cart is empty. Add items before checking out.")

        try:
            # Step 1: Pre-validation of inventory for all items
            for item in cart.items:
                product = self.product_repo.get_by_id(item.product_id)
                if not product or not product.is_active:
                    raise BadRequestException(
                        f"Product '{item.product.title}' is no longer available. Please remove it from your cart."
                    )
                if product.stock_quantity < item.quantity:
                    raise InsufficientStockException(
                        product_title=product.title,
                        available_stock=product.stock_quantity,
                        requested_quantity=item.quantity
                    )

            # Step 2: Calculate total and create order header
            total_amount = sum(round(item.product.price * item.quantity, 2) for item in cart.items)
            order_number = self._generate_order_number()

            order = self.order_repo.create(
                order_number=order_number,
                user_id=user_id,
                total_amount=round(total_amount, 2),
                shipping_address=data.shipping_address,
                contact_phone=data.contact_phone,
                notes=data.notes
            )

            # Step 3: Deduct stock, log inventory movement, and create line items
            for item in cart.items:
                product = self.product_repo.get_by_id(item.product_id)
                subtotal = round(product.price * item.quantity, 2)

                self.order_repo.add_item(
                    order_id=order.id,
                    product_id=product.id,
                    product_title=product.title,
                    unit_price=product.price,
                    quantity=item.quantity,
                    subtotal=subtotal
                )

                previous_stock = product.stock_quantity
                product.stock_quantity -= item.quantity

                self.inventory_repo.record_log(
                    product_id=product.id,
                    change_type=InventoryChangeType.PURCHASE_DEDUCTION,
                    quantity_changed=-item.quantity,
                    previous_quantity=previous_stock,
                    new_quantity=product.stock_quantity,
                    reference_id=order.order_number
                )

            # Step 4: Clear customer's shopping cart
            self.cart_repo.clear(cart.id)

            # Commit the atomic transaction
            self.db.commit()
            self.db.refresh(order)
            return order

        except Exception:
            self.db.rollback()
            raise

    def get_order_by_id(self, order_id: int, current_user_id: int, user_role: UserRole) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order", order_id)

        # Non-admins can only view their own orders
        if user_role != UserRole.ADMIN and order.user_id != current_user_id:
            raise ForbiddenException("You are not authorized to view this order.")

        return order

    def list_user_orders(self, user_id: int, page: int = 1, limit: int = 20) -> Tuple[List[Order], int]:
        skip = (max(1, page) - 1) * limit
        orders = self.order_repo.list_by_user(user_id, skip=skip, limit=limit)
        total = self.order_repo.count_by_user(user_id)
        return orders, total

    def list_all_orders(self, status: Optional[OrderStatus] = None, page: int = 1, limit: int = 50) -> Tuple[List[Order], int]:
        skip = (max(1, page) - 1) * limit
        orders = self.order_repo.list_all(status=status, skip=skip, limit=limit)
        total = self.order_repo.count_all(status=status)
        return orders, total

    def cancel_order(self, order_id: int, current_user_id: int, user_role: UserRole) -> Order:
        """
        Cancels an order and automatically restocks product inventory.
        Customers can cancel PENDING orders. Admins can cancel orders until DELIVERED.
        """
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order", order_id)

        if user_role != UserRole.ADMIN:
            if order.user_id != current_user_id:
                raise ForbiddenException("You are not authorized to cancel this order.")
            if order.status != OrderStatus.PENDING:
                raise BadRequestException(f"Only PENDING orders can be cancelled by customers. Current status: {order.status.value}")
        else:
            if order.status == OrderStatus.DELIVERED:
                raise BadRequestException("Delivered orders cannot be cancelled.")
            if order.status == OrderStatus.CANCELLED:
                raise BadRequestException("Order is already cancelled.")

        try:
            # Restock inventory
            for item in order.items:
                if item.product_id:
                    product = self.product_repo.get_by_id(item.product_id)
                    if product:
                        previous_stock = product.stock_quantity
                        product.stock_quantity += item.quantity

                        self.inventory_repo.record_log(
                            product_id=product.id,
                            change_type=InventoryChangeType.CANCELLATION_RESTOCK,
                            quantity_changed=item.quantity,
                            previous_quantity=previous_stock,
                            new_quantity=product.stock_quantity,
                            reference_id=f"Order cancellation {order.order_number}"
                        )

            order.status = OrderStatus.CANCELLED
            self.db.commit()
            self.db.refresh(order)
            return order

        except Exception:
            self.db.rollback()
            raise

    def update_order_status(self, order_id: int, data: OrderStatusUpdate) -> Order:
        """Admin updates order status (e.g. PENDING -> CONFIRMED -> SHIPPED -> DELIVERED)."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order", order_id)

        if order.status == OrderStatus.CANCELLED:
            raise BadRequestException("Cannot update status of an already cancelled order.")
        if order.status == OrderStatus.DELIVERED:
            raise BadRequestException("Delivered orders have concluded their lifecycle.")

        if data.status == OrderStatus.CANCELLED:
            return self.cancel_order(order_id=order_id, current_user_id=order.user_id, user_role=UserRole.ADMIN)

        order.status = data.status
        self.db.commit()
        self.db.refresh(order)
        return order
