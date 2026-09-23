"""
Inventory Repository
Maintains the audit log of stock movements.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.inventory_log import InventoryLog, InventoryChangeType


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_log(
        self,
        product_id: int,
        change_type: InventoryChangeType,
        quantity_changed: int,
        previous_quantity: int,
        new_quantity: int,
        reference_id: Optional[str] = None
    ) -> InventoryLog:
        log = InventoryLog(
            product_id=product_id,
            change_type=change_type,
            quantity_changed=quantity_changed,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reference_id=reference_id
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_logs(self, product_id: Optional[int] = None, skip: int = 0, limit: int = 50) -> List[InventoryLog]:
        query = self.db.query(InventoryLog)
        if product_id:
            query = query.filter(InventoryLog.product_id == product_id)
        return query.order_by(InventoryLog.id.desc()).offset(skip).limit(limit).all()

    def count_logs(self, product_id: Optional[int] = None) -> int:
        query = self.db.query(InventoryLog)
        if product_id:
            query = query.filter(InventoryLog.product_id == product_id)
        return query.count()
