"""
Request Validation Middleware

Validates incoming requests for security and data integrity.
"""

import re
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RequestValidator:
    """Request validation for security."""
    
    # Maximum request sizes
    MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_QUERY_LENGTH = 2048
    MAX_HEADER_SIZE = 8192
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--|\#|\/\*)",
        r"(\bEXEC\b|\bEXECUTE\b)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
    ]
    
    def __init__(self):
        """Initialize validator."""
        self.sql_regex = re.compile(
            "|".join(self.SQL_INJECTION_PATTERNS),
            re.IGNORECASE
        )
        self.xss_regex = re.compile(
            "|".join(self.XSS_PATTERNS),
            re.IGNORECASE
        )
        self.path_regex = re.compile(
            "|".join(self.PATH_TRAVERSAL_PATTERNS),
            re.IGNORECASE
        )
    
    def validate_request_size(self, request: Request) -> Optional[str]:
        """
        Validate request size.
        
        Args:
            request: FastAPI request
            
        Returns:
            Error message if invalid, None if valid
        """
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.MAX_JSON_SIZE:
                    return f"Request body too large. Maximum {self.MAX_JSON_SIZE} bytes"
            except ValueError:
                return "Invalid content-length header"
        
        # Check query string length
        if len(str(request.url.query)) > self.MAX_QUERY_LENGTH:
            return f"Query string too long. Maximum {self.MAX_QUERY_LENGTH} characters"
        
        # Check header size
        header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if header_size > self.MAX_HEADER_SIZE:
            return f"Headers too large. Maximum {self.MAX_HEADER_SIZE} bytes"
        
        return None
    
    def check_sql_injection(self, value: str) -> bool:
        """
        Check for SQL injection patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if suspicious pattern found
        """
        return bool(self.sql_regex.search(value))
    
    def check_xss(self, value: str) -> bool:
        """
        Check for XSS patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if suspicious pattern found
        """
        return bool(self.xss_regex.search(value))
    
    def check_path_traversal(self, value: str) -> bool:
        """
        Check for path traversal patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if suspicious pattern found
        """
        return bool(self.path_regex.search(value))
    
    def validate_string(self, value: str, field_name: str) -> Optional[str]:
        """
        Validate string for security issues.
        
        Args:
            value: String to validate
            field_name: Name of field for error message
            
        Returns:
            Error message if invalid, None if valid
        """
        if self.check_sql_injection(value):
            logger.warning(f"SQL injection attempt detected in {field_name}: {value[:100]}")
            return f"Invalid characters in {field_name}"
        
        if self.check_xss(value):
            logger.warning(f"XSS attempt detected in {field_name}: {value[:100]}")
            return f"Invalid characters in {field_name}"
        
        if self.check_path_traversal(value):
            logger.warning(f"Path traversal attempt detected in {field_name}: {value[:100]}")
            return f"Invalid characters in {field_name}"
        
        return None


# Global validator instance
validator = RequestValidator()


async def validation_middleware(request: Request, call_next):
    """
    Request validation middleware.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response or 400 Bad Request
    """
    # Validate request size
    size_error = validator.validate_request_size(request)
    if size_error:
        logger.warning(f"Request size validation failed: {size_error}")
        return JSONResponse(
            status_code=400,
            content={"error": "Bad Request", "message": size_error}
        )
    
    # Validate query parameters
    for key, value in request.query_params.items():
        error = validator.validate_string(str(value), f"query parameter '{key}'")
        if error:
            return JSONResponse(
                status_code=400,
                content={"error": "Bad Request", "message": error}
            )
    
    # Validate path parameters
    for key, value in request.path_params.items():
        error = validator.validate_string(str(value), f"path parameter '{key}'")
        if error:
            return JSONResponse(
                status_code=400,
                content={"error": "Bad Request", "message": error}
            )
    
    response = await call_next(request)
    return response
