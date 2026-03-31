"""
Validation utilities for Avenlis.

This module provides validation functions for various data types
and formats used in the Avenlis library.
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from sandstrike.exceptions import AvenlisValidationError


def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Validate a URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_api_key(api_key: str) -> bool:
    """
    Validate an API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Basic validation - adjust based on your API key format
    api_key = api_key.strip()
    return len(api_key) >= 10 and not any(char.isspace() for char in api_key)


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Raises:
        AvenlisValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise AvenlisValidationError(f"Missing required fields: {', '.join(missing_fields)}")


def validate_string_length(value: str, min_length: int = 0, max_length: Optional[int] = None, field_name: str = "field") -> None:
    """
    Validate string length constraints.
    
    Args:
        value: String value to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length (None for no limit)
        field_name: Name of the field being validated
        
    Raises:
        AvenlisValidationError: If length constraints are violated
    """
    if not isinstance(value, str):
        raise AvenlisValidationError(f"{field_name} must be a string")
    
    if len(value) < min_length:
        raise AvenlisValidationError(f"{field_name} must be at least {min_length} characters long")
    
    if max_length is not None and len(value) > max_length:
        raise AvenlisValidationError(f"{field_name} must be no more than {max_length} characters long")
