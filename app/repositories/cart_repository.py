"""
Cart Repository
Database operations for shopping carts and cart items.
"""

from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.models.cart import Cart, CartItem


class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Optional[Cart]:
        return self.db.query(Cart).options(
            joinedload(Cart.items).joinedload(CartItem.product)
        ).filter(Cart.user_id == user_id).first()

    def get_or_create(self, user_id: int) -> Cart:
        cart = self.get_by_user_id(user_id)
        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        return cart

    def get_item(self, cart_id: int, product_id: int) -> Optional[CartItem]:
        return self.db.query(CartItem).filter(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id
        ).first()

    def add_or_update_item(self, cart_id: int, product_id: int, quantity_to_add: int) -> CartItem:
        item = self.get_item(cart_id, product_id)
        if item:
            item.quantity += quantity_to_add
        else:
            item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity_to_add)
            self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def set_item_quantity(self, cart_id: int, product_id: int, new_quantity: int) -> Optional[CartItem]:
        item = self.get_item(cart_id, product_id)
        if not item:
            return None
        if new_quantity <= 0:
            self.db.delete(item)
            self.db.commit()
            return None
        item.quantity = new_quantity
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_item(self, cart_id: int, product_id: int) -> bool:
        item = self.get_item(cart_id, product_id)
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False

    def clear(self, cart_id: int) -> None:
        self.db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
        self.db.commit()
