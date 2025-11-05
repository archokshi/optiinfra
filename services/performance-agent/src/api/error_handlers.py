"""
Error Handlers

Global error handlers for FastAPI application.
"""

import logging
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.models.errors import ErrorResponse, ErrorDetail, ValidationErrorResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    details = []
    invalid_fields = []
    
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        invalid_fields.append(field)
        details.append(ErrorDetail(
            field=field,
            message=error["msg"],
            type=error["type"]
        ))
    
    error_response = ValidationErrorResponse(
        message="Request validation failed",
        details=details,
        invalid_fields=invalid_fields,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception on {request.url.path}: {exc.detail}")
    
    error_response = ErrorResponse(
        error=f"http_{exc.status_code}",
        message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    
    error_response = ErrorResponse(
        error="internal_server_error",
        message="An unexpected error occurred",
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )
