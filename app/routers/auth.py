"""
Authentication Router
Public endpoints for registration and login, plus current user identity inspection.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import api_success
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.routers.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    summary="Register a new user account",
    description="Registers a customer or admin account. Initializes an empty shopping cart automatically.",
    status_code=status.HTTP_201_CREATED
)
def register(data: UserRegister, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.register(data)
    return api_success(
        message="User account registered successfully.",
        data=user.model_dump(),
        status_code=status.HTTP_201_CREATED
    )


@router.post(
    "/login",
    summary="Authenticate user and receive JWT",
    description="Validates email and password, returning an access token (Bearer) valid for 24 hours.",
    status_code=status.HTTP_200_OK
)
def login(data: UserLogin, db: Session = Depends(get_db)):
    service = AuthService(db)
    token_response = service.login(data)
    return api_success(
        message="Login successful.",
        data=token_response.model_dump(),
        status_code=status.HTTP_200_OK
    )


@router.get(
    "/me",
    summary="Get current authenticated user profile",
    description="Inspects the provided JWT Bearer token and returns the caller's profile.",
    status_code=status.HTTP_200_OK
)
def get_me(current_user: User = Depends(get_current_user)):
    user_response = UserResponse.model_validate(current_user)
    return api_success(
        message="Profile retrieved successfully.",
        data=user_response.model_dump(),
        status_code=status.HTTP_200_OK
    )
