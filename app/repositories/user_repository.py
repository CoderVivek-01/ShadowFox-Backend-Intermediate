"""
User Repository
Encapsulates database operations for the User entity.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower().strip()).first()

    def create(self, full_name: str, email: str, hashed_password: str, role: UserRole = UserRole.CUSTOMER) -> User:
        user = User(
            full_name=full_name.strip(),
            email=email.lower().strip(),
            hashed_password=hashed_password,
            role=role,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def count(self) -> int:
        return self.db.query(User).count()

    def list_all(self, skip: int = 0, limit: int = 50) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()
