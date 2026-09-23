"""
Category Repository
Database operations for product categories.
"""

import re
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.category import Category


def slugify(text: str) -> str:
    """Helper to convert category name into URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_by_name(self, name: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.name.ilike(name.strip())).first()

    def get_by_slug(self, slug: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.slug == slug).first()

    def list_all(self, only_active: bool = False) -> List[Category]:
        query = self.db.query(Category)
        if only_active:
            query = query.filter(Category.is_active == True)
        return query.order_by(Category.name.asc()).all()

    def create(self, name: str, description: Optional[str] = None) -> Category:
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while self.get_by_slug(slug) is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1

        category = Category(
            name=name.strip(),
            slug=slug,
            description=description,
            is_active=True
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category, name: Optional[str] = None, description: Optional[str] = None, is_active: Optional[bool] = None) -> Category:
        if name is not None and name.strip() != category.name:
            category.name = name.strip()
            category.slug = slugify(name)
        if description is not None:
            category.description = description
        if is_active is not None:
            category.is_active = is_active
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()
