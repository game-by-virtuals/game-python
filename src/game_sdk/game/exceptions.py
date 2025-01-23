"""
Custom exceptions for the GAME SDK.

This module defines all custom exceptions that can be raised by the SDK,
making error handling more specific and informative.
"""

class GameSDKError(Exception):
    """Base exception class for all GAME SDK errors."""
    pass


class APIError(GameSDKError):
    """Raised when there's an error communicating with the GAME API."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class AuthenticationError(APIError):
    """Raised when there's an authentication error with the API."""
    pass


class ConfigurationError(GameSDKError):
    """Raised when there's an error in the SDK configuration."""
    pass


class ValidationError(GameSDKError):
    """Raised when there's an error validating input data."""
    pass


class FunctionExecutionError(GameSDKError):
    """Raised when there's an error executing a function."""
    def __init__(self, function_name: str, message: str, original_error: Exception = None):
        self.function_name = function_name
        self.original_error = original_error
        super().__init__(f"Error executing function '{function_name}': {message}")


class WorkerError(GameSDKError):
    """Raised when there's an error with worker operations."""
    pass


class AgentError(GameSDKError):
    """Raised when there's an error with agent operations."""
    pass
