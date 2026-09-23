"""
FastAPI Dependencies & RBAC Guards
Extracts authenticated user from JWT Bearer token and enforces role-based access control.
"""

from typing import List
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

# HTTPBearer extracts "Authorization: Bearer <token>"
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the JWT access token and retrieves the current authenticated user.
    Raises 401 Unauthorized if token is missing, invalid, expired, or user is deactivated.
    """
    if not credentials:
        raise UnauthorizedException("Authentication token is missing. Please provide a Bearer token.")

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired authentication token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload is missing user subject.")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(int(user_id_str))
    if not user:
        raise UnauthorizedException("Authenticated user account no longer exists.")

    if not user.is_active:
        raise UnauthorizedException("User account has been deactivated.")

    return user


def require_roles(allowed_roles: List[UserRole]):
    """
    Role-Based Access Control (RBAC) factory dependency.
    Validates that the authenticated user possesses one of the allowed roles.
    Raises 403 Forbidden if user lacks sufficient privileges.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                f"Access denied: Required role '{', '.join([r.value for r in allowed_roles])}', but you have '{current_user.role.value}'."
            )
        return current_user
    return role_checker


# Convenient RBAC shorthands
get_current_admin = require_roles([UserRole.ADMIN])
get_current_customer = require_roles([UserRole.CUSTOMER, UserRole.ADMIN])
