"""
Data Validation Utilities

Common validators for data validation.
"""

import re
from typing import Any, List, Optional
from datetime import datetime


class ValidationError(Exception):
    """Validation error exception"""
    pass


def validate_required(value: Any, field_name: str):
    """Validate that a value is not None or empty"""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f"{field_name} is required")


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


def validate_range(value: float, min_val: float = None, max_val: float = None, field_name: str = "Value"):
    """Validate that a value is within a range"""
    if min_val is not None and value < min_val:
        raise ValidationError(f"{field_name} must be >= {min_val}")
    if max_val is not None and value > max_val:
        raise ValidationError(f"{field_name} must be <= {max_val}")


def validate_length(value: str, min_length: int = None, max_length: int = None, field_name: str = "Value"):
    """Validate string length"""
    length = len(value)
    if min_length is not None and length < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    if max_length is not None and length > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")


def validate_in_list(value: Any, valid_values: List[Any], field_name: str = "Value"):
    """Validate that a value is in a list of valid values"""
    if value not in valid_values:
        raise ValidationError(f"{field_name} must be one of: {', '.join(map(str, valid_values))}")


def validate_datetime_format(date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> bool:
    """Validate datetime string format"""
    try:
        datetime.strptime(date_string, format_string)
        return True
    except ValueError:
        return False


def validate_positive(value: float, field_name: str = "Value"):
    """Validate that a value is positive"""
    if value <= 0:
        raise ValidationError(f"{field_name} must be positive")


def validate_non_negative(value: float, field_name: str = "Value"):
    """Validate that a value is non-negative"""
    if value < 0:
        raise ValidationError(f"{field_name} must be non-negative")


def validate_instance_id(instance_id: str) -> bool:
    """Validate cloud instance ID format"""
    # AWS: i-xxxxxxxxxxxxxxxxx (17 chars after i-)
    # GCP: instance-name (lowercase, hyphens)
    # Azure: vm-name (alphanumeric, hyphens, underscores)
    patterns = [
        r'^i-[a-f0-9]{17}$',  # AWS
        r'^[a-z][-a-z0-9]{0,62}$',  # GCP
        r'^[a-zA-Z0-9][-a-zA-Z0-9_]{0,63}$',  # Azure
    ]
    return any(re.match(pattern, instance_id) for pattern in patterns)


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string by removing special characters and limiting length"""
    # Remove control characters
    sanitized = ''.join(char for char in value if ord(char) >= 32)
    # Limit length
    return sanitized[:max_length]
