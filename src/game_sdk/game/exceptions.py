"""
Custom exceptions for the GAME SDK.

This module defines the exception hierarchy used throughout the GAME SDK.
All exceptions inherit from the base GameSDKError class, providing a consistent
error handling interface.

Exception Hierarchy:
    GameSDKError
    ├── ValidationError
    ├── APIError
    │   └── AuthenticationError
    └── StateError

Example:
    try:
        agent = Agent(api_key="invalid_key", ...)
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except ValidationError as e:
        print(f"Validation failed: {e}")
    except APIError as e:
        print(f"API error: {e}")
"""

class GameSDKError(Exception):
    """Base exception class for all GAME SDK errors.

    This is the parent class for all custom exceptions in the SDK.
    It inherits from the built-in Exception class and serves as a
    way to catch all SDK-specific exceptions.

    Example:
        try:
            # SDK operation
        except GameSDKError as e:
            print(f"SDK operation failed: {e}")
    """
    pass

class ValidationError(GameSDKError):
    """Raised when input validation fails.

    This exception is raised when input parameters fail validation,
    such as empty strings, invalid types, or invalid formats.

    Args:
        message (str): Human-readable error description
        errors (dict, optional): Dictionary containing validation errors

    Example:
        raise ValidationError("Name cannot be empty", {"name": "required"})
    """
    def __init__(self, message="Validation failed", errors=None):
        super().__init__(message)
        self.errors = errors or {}

class APIError(GameSDKError):
    """Raised when API requests fail.

    This exception is raised for any API-related errors, including network
    issues, server errors, and invalid responses.

    Args:
        message (str): Human-readable error description
        status_code (int, optional): HTTP status code if applicable
        response_json (dict, optional): Raw response data from the API

    Example:
        raise APIError("Failed to create agent", status_code=500)
    """
    def __init__(self, message="API request failed", status_code=None, response_json=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_json = response_json

class AuthenticationError(APIError):
    """Raised when authentication fails.

    This exception is raised for authentication-specific failures,
    such as invalid API keys or expired tokens.

    Example:
        raise AuthenticationError("Invalid API key")
    """
    pass

class StateError(GameSDKError):
    """Raised when there are issues with state management.

    This exception is raised when there are problems with agent or
    worker state management, such as invalid state transitions or
    corrupted state data.

    Example:
        raise StateError("Invalid state transition")
    """
    pass
