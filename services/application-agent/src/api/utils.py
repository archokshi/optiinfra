"""
API Utilities

Helper functions for API endpoints.
"""

from typing import List, Dict, Any, Optional, Callable
from fastapi import HTTPException, status, Query
from functools import wraps
from ..core.logger import logger


def paginate(
    items: List[Any],
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Paginated response with metadata
    """
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": items[start:end],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


def validate_pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100)
) -> Dict[str, int]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number
        page_size: Page size
        
    Returns:
        Validated pagination parameters
    """
    return {"page": page, "page_size": page_size}


def format_error_response(
    error: Exception,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> Dict[str, Any]:
    """
    Format error response.
    
    Args:
        error: Exception
        status_code: HTTP status code
        
    Returns:
        Formatted error response
    """
    return {
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "status_code": status_code
        }
    }


def handle_api_errors(func: Callable) -> Callable:
    """
    Decorator to handle API errors.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    return wrapper


def validate_model_id(model_id: str) -> str:
    """
    Validate model ID format.
    
    Args:
        model_id: Model identifier
        
    Returns:
        Validated model ID
        
    Raises:
        HTTPException: If model ID is invalid
    """
    if not model_id or len(model_id) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model ID"
        )
    return model_id


def validate_quality_score(score: float) -> float:
    """
    Validate quality score.
    
    Args:
        score: Quality score
        
    Returns:
        Validated score
        
    Raises:
        HTTPException: If score is invalid
    """
    if not 0 <= score <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quality score must be between 0 and 100"
        )
    return score
