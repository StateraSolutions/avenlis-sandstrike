"""
Exception classes for Avenlis.

This module defines custom exception classes used throughout
the Avenlis library and CLI.
"""


class AvenlisError(Exception):
    """Base exception class for all Avenlis-related errors."""
    pass


class AvenlisAuthError(AvenlisError):
    """Exception raised for authentication-related errors."""
    pass


class AvenlisAPIError(AvenlisError):
    """Exception raised for API-related errors."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class AvenlisConfigError(AvenlisError):
    """Exception raised for configuration-related errors."""
    pass


class AvenlisValidationError(AvenlisError):
    """Exception raised for validation errors."""
    pass


class AvenlisNetworkError(AvenlisError):
    """Exception raised for network-related errors."""
    pass
