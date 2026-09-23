"""
Authentication Service
Encapsulates registration, credentials verification, and token issuance.
"""

from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.repositories.user_repository import UserRepository
from app.repositories.cart_repository import CartRepository
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException, BadRequestException


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.cart_repo = CartRepository(db)

    def register(self, data: UserRegister) -> UserResponse:
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException(f"User with email '{data.email}' is already registered.")

        hashed_pwd = get_password_hash(data.password)
        user = self.user_repo.create(
            full_name=data.full_name,
            email=data.email,
            hashed_password=hashed_pwd,
            role=data.role or UserRole.CUSTOMER
        )
        # Pre-initialize user's shopping cart
        self.cart_repo.get_or_create(user.id)
        return UserResponse.model_validate(user)

    def login(self, data: UserLogin) -> TokenResponse:
        user = self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")

        if not user.is_active:
            raise BadRequestException("Your account has been deactivated. Please contact support.")

        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
        access_token = create_access_token(token_payload)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
