"""
Categories Router
Public catalog browsing and Admin-restricted category management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import api_success
from app.core.exceptions import EntityNotFoundException, ConflictException
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.repositories.category_repository import CategoryRepository
from app.routers.deps import get_current_admin

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    summary="List all product categories",
    description="Returns active categories. Anyone (public or authenticated) can browse categories.",
    status_code=status.HTTP_200_OK
)
def list_categories(
    all_categories: bool = Query(False, description="If true, includes inactive categories (Admin)"),
    db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    categories = repo.list_all(only_active=not all_categories)
    data = [CategoryResponse.model_validate(c).model_dump() for c in categories]
    return api_success(
        message="Categories retrieved successfully.",
        data=data
    )


@router.get(
    "/{category_id}",
    summary="Get category details by ID",
    status_code=status.HTTP_200_OK
)
def get_category(category_id: int, db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    category = repo.get_by_id(category_id)
    if not category:
        raise EntityNotFoundException("Category", category_id)
    return api_success(
        message="Category details retrieved.",
        data=CategoryResponse.model_validate(category).model_dump()
    )


@router.post(
    "",
    summary="Create a new category (Admin Only)",
    description="Protected endpoint for store administrators to create categories.",
    status_code=status.HTTP_201_CREATED
)
def create_category(
    data: CategoryCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    if repo.get_by_name(data.name):
        raise ConflictException(f"Category with name '{data.name}' already exists.")

    category = repo.create(name=data.name, description=data.description)
    return api_success(
        message="Category created successfully.",
        data=CategoryResponse.model_validate(category).model_dump(),
        status_code=status.HTTP_201_CREATED
    )


@router.put(
    "/{category_id}",
    summary="Update category (Admin Only)",
    status_code=status.HTTP_200_OK
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    category = repo.get_by_id(category_id)
    if not category:
        raise EntityNotFoundException("Category", category_id)

    updated = repo.update(category, **data.model_dump(exclude_unset=True))
    return api_success(
        message="Category updated successfully.",
        data=CategoryResponse.model_validate(updated).model_dump()
    )


@router.delete(
    "/{category_id}",
    summary="Delete category (Admin Only)",
    status_code=status.HTTP_200_OK
)
def delete_category(
    category_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    repo = CategoryRepository(db)
    category = repo.get_by_id(category_id)
    if not category:
        raise EntityNotFoundException("Category", category_id)

    repo.delete(category)
    return api_success(message=f"Category '{category.name}' deleted successfully.")
