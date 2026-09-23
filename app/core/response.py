"""
Standardized API Response Envelopes
Ensures all API endpoints return consistent JSON contracts for predictable client integration.
"""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

T = TypeVar("T")


class ResponseMetadata(BaseModel):
    page: Optional[int] = None
    limit: Optional[int] = None
    total: Optional[int] = None
    total_pages: Optional[int] = None


class StandardSuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None
    meta: Optional[ResponseMetadata] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class StandardErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


def api_success(
    message: str = "Operation completed successfully",
    data: Optional[Any] = None,
    meta: Optional[ResponseMetadata] = None,
    status_code: int = 200
) -> JSONResponse:
    """Helper to return a standardized JSON success response."""
    payload = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta is not None:
        payload["meta"] = meta.model_dump()
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))
