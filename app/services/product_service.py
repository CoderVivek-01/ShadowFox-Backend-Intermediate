"""
Product and Inventory Service
Enforces product catalog validity and stock level integrity.
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.inventory_log import InventoryChangeType
from app.schemas.product import ProductCreate, ProductUpdate, StockAdjustmentRequest
from app.repositories.product_repository import ProductRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.inventory_repository import InventoryRepository
from app.core.exceptions import EntityNotFoundException, ConflictException, BadRequestException


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.inventory_repo = InventoryRepository(db)

    def get_by_id(self, product_id: int) -> Product:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Product", product_id)
        return product

    def get_by_slug(self, slug: str) -> Product:
        product = self.product_repo.get_by_slug(slug)
        if not product:
            raise EntityNotFoundException("Product", slug)
        return product

    def list_products(
        self,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        only_active: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Product], int]:
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
        skip = (page - 1) * limit

        items = self.product_repo.list_filtered(
            category_id=category_id,
            search=search,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            only_active=only_active,
            skip=skip,
            limit=limit
        )
        total = self.product_repo.count_filtered(
            category_id=category_id,
            search=search,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            only_active=only_active
        )
        return items, total

    def create_product(self, data: ProductCreate) -> Product:
        # Verify category exists and is active
        category = self.category_repo.get_by_id(data.category_id)
        if not category:
            raise EntityNotFoundException("Category", data.category_id)
        if not category.is_active:
            raise BadRequestException("Cannot create a product in an inactive category.")

        # Check SKU uniqueness
        if self.product_repo.get_by_sku(data.sku):
            raise ConflictException(f"A product with SKU '{data.sku}' already exists.")

        product = self.product_repo.create(
            category_id=data.category_id,
            title=data.title,
            sku=data.sku,
            price=data.price,
            stock_quantity=data.stock_quantity,
            description=data.description,
            is_active=True
        )

        # Record initial stock log
        if data.stock_quantity > 0:
            self.inventory_repo.record_log(
                product_id=product.id,
                change_type=InventoryChangeType.INITIAL_STOCK,
                quantity_changed=data.stock_quantity,
                previous_quantity=0,
                new_quantity=data.stock_quantity,
                reference_id="Initial product creation"
            )
            self.db.commit()

        return product

    def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get_by_id(product_id)

        if data.category_id is not None and data.category_id != product.category_id:
            category = self.category_repo.get_by_id(data.category_id)
            if not category:
                raise EntityNotFoundException("Category", data.category_id)

        if data.sku is not None and data.sku.upper() != product.sku:
            existing_sku = self.product_repo.get_by_sku(data.sku)
            if existing_sku and existing_sku.id != product.id:
                raise ConflictException(f"A product with SKU '{data.sku}' already exists.")

        update_dict = data.model_dump(exclude_unset=True)
        # If stock quantity is updated directly, log the delta
        if "stock_quantity" in update_dict:
            new_stock = update_dict["stock_quantity"]
            delta = new_stock - product.stock_quantity
            if delta != 0:
                self.inventory_repo.record_log(
                    product_id=product.id,
                    change_type=InventoryChangeType.MANUAL_ADJUSTMENT,
                    quantity_changed=delta,
                    previous_quantity=product.stock_quantity,
                    new_quantity=new_stock,
                    reference_id="Direct stock overwrite"
                )

        updated_product = self.product_repo.update(product, **update_dict)
        return updated_product

    def delete_product(self, product_id: int) -> None:
        product = self.get_by_id(product_id)
        self.product_repo.delete(product)

    def adjust_stock(self, product_id: int, request: StockAdjustmentRequest) -> Product:
        product = self.get_by_id(product_id)
        current_stock = product.stock_quantity
        new_stock = current_stock + request.adjustment

        if new_stock < 0:
            raise BadRequestException(
                f"Cannot adjust stock by {request.adjustment}. Current stock is {current_stock}, resulting stock would be negative."
            )

        product.stock_quantity = new_stock
        change_type = InventoryChangeType.RESTOCK if request.adjustment > 0 else InventoryChangeType.MANUAL_ADJUSTMENT

        self.inventory_repo.record_log(
            product_id=product.id,
            change_type=change_type,
            quantity_changed=request.adjustment,
            previous_quantity=current_stock,
            new_quantity=new_stock,
            reference_id=request.reason
        )
        self.db.commit()
        self.db.refresh(product)
        return product
