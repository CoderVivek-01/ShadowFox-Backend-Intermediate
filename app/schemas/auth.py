"""
Authentication and User Pydantic Schemas
Strict input validation for user registration, login, and profile output.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the user", examples=["John Doe"])
    email: EmailStr = Field(..., description="Valid unique email address", examples=["john@example.com"])
    password: str = Field(..., min_length=6, max_length=100, description="Password (at least 6 characters)", examples=["SecureP@ss123"])
    role: Optional[UserRole] = Field(default=UserRole.CUSTOMER, description="Role: customer or admin (default customer)")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Registered email", examples=["john@example.com"])
    password: str = Field(..., description="Account password", examples=["SecureP@ss123"])


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
