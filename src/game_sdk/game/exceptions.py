"""
Custom exceptions for the GAME SDK.

This module provides custom exception classes for better error handling
and more informative error messages.
"""


class GameSDKError(Exception):
    """Base exception class for all GAME SDK errors."""
    pass


class APIError(GameSDKError):
    """Raised when an API request fails."""
    pass


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass


class ValidationError(APIError):
    """Raised when request validation fails."""
    pass
