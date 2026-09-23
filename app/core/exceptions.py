"""
Domain-Specific Custom Exceptions
Used across repositories and services to signal specific business rule violations.
These exceptions are intercepted by the global error handler middleware.
"""

from typing import Optional, Any


class AppException(Exception):
    """Base application exception with error code and status code."""
    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST", details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class EntityNotFoundException(AppException):
    """Raised when a requested resource does not exist."""
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            status_code=404,
            code="NOT_FOUND"
        )


class BadRequestException(AppException):
    """Raised when client input violates application business rules."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            code="BAD_REQUEST",
            details=details
        )


class InsufficientStockException(AppException):
    """
    Raised when requested order/cart quantity exceeds currently available warehouse inventory.
    Enforces the core business rule mandated by ShadowFox.
    """
    def __init__(self, product_title: str, available_stock: int, requested_quantity: int):
        super().__init__(
            message=f"Insufficient stock for '{product_title}'. Available: {available_stock}, Requested: {requested_quantity}.",
            status_code=409,
            code="INSUFFICIENT_STOCK",
            details={
                "product": product_title,
                "available_stock": available_stock,
                "requested_quantity": requested_quantity
            }
        )


class UnauthorizedException(AppException):
    """Raised when authentication credentials are missing, invalid, or expired."""
    def __init__(self, message: str = "Could not validate authentication credentials."):
        super().__init__(
            message=message,
            status_code=401,
            code="UNAUTHORIZED"
        )


class ForbiddenException(AppException):
    """Raised when an authenticated user does not have permission (RBAC)."""
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            message=message,
            status_code=403,
            code="FORBIDDEN"
        )


class ConflictException(AppException):
    """Raised when a resource already exists (e.g. duplicate email or SKU)."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=409,
            code="CONFLICT"
        )
