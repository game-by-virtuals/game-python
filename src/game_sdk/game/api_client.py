"""
API client module for the GAME SDK.

This module provides a dedicated API client for making requests to the GAME API,
handling authentication, errors, and response parsing consistently.
"""

import requests
from typing import Dict, Any, Optional
from game_sdk.game.config import config
from game_sdk.game.exceptions import APIError, AuthenticationError, ValidationError
from game_sdk.game.custom_types import ActionResponse, FunctionResult
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception


class GameAPIClient:
    """Client for interacting with the GAME API.

    This class handles all API communication, including authentication,
    request retries, and error handling.

    Attributes:
        api_key (str): API key for authentication
        base_url (str): Base URL for API requests
        session (requests.Session): Reusable session for API requests
    """

    def __init__(self, api_key: str):
        """Initialize the API client.

        Args:
            api_key (str): API key for authentication

        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = config.api_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    @staticmethod
    def should_retry(exception):
        """Determine if we should retry the request based on the exception type."""
        if isinstance(exception, (AuthenticationError, ValidationError)):
            return False
        return isinstance(exception, (APIError, requests.exceptions.RequestException))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception(should_retry)
    )
    def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            data (Optional[Dict[str, Any]], optional): Request body. Defaults to None.
            params (Optional[Dict[str, Any]], optional): Query parameters. Defaults to None.

        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If request validation fails
            APIError: For other API-related errors

        Returns:
            Dict[str, Any]: API response data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                # Don't retry auth errors
                raise AuthenticationError("Authentication failed") from e
            elif response.status_code == 422:
                # Don't retry validation errors
                raise ValidationError("Invalid request data") from e
            else:
                # Retry other HTTP errors
                raise APIError(f"API request failed: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            # Retry network errors
            raise APIError(f"Request failed: {str(e)}") from e

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint (str): API endpoint
            params (Optional[Dict[str, Any]], optional): Query parameters. Defaults to None.

        Returns:
            Dict[str, Any]: API response data
        """
        return self.make_request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any]): Request body

        Returns:
            Dict[str, Any]: API response data
        """
        return self.make_request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request.

        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any]): Request body

        Returns:
            Dict[str, Any]: API response data
        """
        return self.make_request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request.

        Args:
            endpoint (str): API endpoint

        Returns:
            Dict[str, Any]: API response data
        """
        return self.make_request("DELETE", endpoint)
