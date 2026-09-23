"""
Inventory Audit Log Model
Tracks all historical inventory changes (purchases, restocks, cancellations, adjustments).
Provides auditability for warehouse and e-commerce stock consistency.
"""

from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base


class InventoryChangeType(str, enum.Enum):
    INITIAL_STOCK = "INITIAL_STOCK"
    RESTOCK = "RESTOCK"
    PURCHASE_DEDUCTION = "PURCHASE_DEDUCTION"
    CANCELLATION_RESTOCK = "CANCELLATION_RESTOCK"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"


class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    change_type = Column(Enum(InventoryChangeType), nullable=False)
    quantity_changed = Column(Integer, nullable=False)
    previous_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    reference_id = Column(String(100), nullable=True)  # e.g., order_number or admin note
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="inventory_logs")

    def __repr__(self) -> str:
        return f"<InventoryLog product_id={self.product_id} change={self.quantity_changed} ({self.change_type.value})>"
