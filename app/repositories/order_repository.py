"""
Order Repository
Database transactions for orders and line items.
"""

from typing import Optional, List
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.order import Order, OrderItem, OrderStatus


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.db.query(Order).options(
            joinedload(Order.items)
        ).filter(Order.id == order_id).first()

    def get_by_number(self, order_number: str) -> Optional[Order]:
        return self.db.query(Order).options(
            joinedload(Order.items)
        ).filter(Order.order_number == order_number).first()

    def list_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> List[Order]:
        return self.db.query(Order).options(
            joinedload(Order.items)
        ).filter(Order.user_id == user_id).order_by(Order.id.desc()).offset(skip).limit(limit).all()

    def count_by_user(self, user_id: int) -> int:
        return self.db.query(Order).filter(Order.user_id == user_id).count()

    def list_all(self, status: Optional[OrderStatus] = None, skip: int = 0, limit: int = 50) -> List[Order]:
        query = self.db.query(Order).options(joinedload(Order.items))
        if status:
            query = query.filter(Order.status == status)
        return query.order_by(Order.id.desc()).offset(skip).limit(limit).all()

    def count_all(self, status: Optional[OrderStatus] = None) -> int:
        query = self.db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        return query.count()

    def get_total_revenue(self) -> float:
        # Sum only confirmed, shipped, or delivered orders
        result = self.db.query(func.sum(Order.total_amount)).filter(
            Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED])
        ).scalar()
        return round(float(result or 0.0), 2)

    def create(
        self,
        order_number: str,
        user_id: int,
        total_amount: float,
        shipping_address: str,
        contact_phone: str,
        notes: Optional[str] = None
    ) -> Order:
        order = Order(
            order_number=order_number,
            user_id=user_id,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            shipping_address=shipping_address,
            contact_phone=contact_phone,
            notes=notes
        )
        self.db.add(order)
        self.db.flush()  # Populates order.id before creating items in the same transaction
        return order

    def add_item(
        self,
        order_id: int,
        product_id: Optional[int],
        product_title: str,
        unit_price: float,
        quantity: int,
        subtotal: float
    ) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            product_title=product_title,
            unit_price=unit_price,
            quantity=quantity,
            subtotal=subtotal
        )
        self.db.add(item)
        return item

    def update_status(self, order: Order, new_status: OrderStatus) -> Order:
        order.status = new_status
        self.db.commit()
        self.db.refresh(order)
        return order
