"""
Error Response Models

Standardized error responses for API.
"""

from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List
from datetime import datetime


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Standardized error response."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = Field(None, description="Request path")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, timestamp: datetime, _info):
        return timestamp.isoformat()


class ValidationErrorResponse(ErrorResponse):
    """Validation error response."""
    
    error: str = "validation_error"
    invalid_fields: List[str] = Field(default_factory=list)
