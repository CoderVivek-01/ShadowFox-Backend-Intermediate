"""
Product Repository
Database querying, filtering, search, pagination, and atomic stock modification.
"""

import re
from typing import Optional, List, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.models.product import Product


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).options(joinedload(Product.category)).filter(Product.id == product_id).first()

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.sku == sku.upper().strip()).first()

    def get_by_slug(self, slug: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.slug == slug).first()

    def list_filtered(
        self,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        only_active: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> List[Product]:
        query = self.db.query(Product).options(joinedload(Product.category))

        if only_active:
            query = query.filter(Product.is_active == True)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.title.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.sku.ilike(search_term)
                )
            )
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        if in_stock_only:
            query = query.filter(Product.stock_quantity > 0)

        return query.order_by(Product.id.desc()).offset(skip).limit(limit).all()

    def count_filtered(
        self,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        only_active: bool = True
    ) -> int:
        query = self.db.query(Product)

        if only_active:
            query = query.filter(Product.is_active == True)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.title.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.sku.ilike(search_term)
                )
            )
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        if in_stock_only:
            query = query.filter(Product.stock_quantity > 0)

        return query.count()

    def create(
        self,
        category_id: int,
        title: str,
        sku: str,
        price: float,
        stock_quantity: int = 0,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> Product:
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while self.get_by_slug(slug) is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1

        product = Product(
            category_id=category_id,
            title=title.strip(),
            slug=slug,
            sku=sku.upper().strip(),
            price=price,
            stock_quantity=stock_quantity,
            description=description,
            is_active=is_active
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product: Product, **kwargs) -> Product:
        for key, value in kwargs.items():
            if value is not None and hasattr(product, key):
                if key == "sku":
                    value = value.upper().strip()
                elif key == "title" and value.strip() != product.title:
                    product.slug = slugify(value)
                setattr(product, key, value)
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete(self, product: Product) -> None:
        self.db.delete(product)
        self.db.commit()

    def count_total(self) -> int:
        return self.db.query(Product).count()

    def count_out_of_stock(self) -> int:
        return self.db.query(Product).filter(Product.stock_quantity == 0).count()

    def count_low_stock(self, threshold: int = 5) -> int:
        return self.db.query(Product).filter(Product.stock_quantity > 0, Product.stock_quantity <= threshold).count()
