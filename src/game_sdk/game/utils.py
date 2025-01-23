"""
Utility functions for the GAME SDK.

This module provides utility functions for common operations like
authentication and API communication.
"""

import requests
from typing import List, Dict, Any, Optional
from .config import config
from .exceptions import (
    APIError,
    AuthenticationError,
    ValidationError
)


def get_access_token(api_key: str) -> str:
    """
    Get an access token from the GAME API.

    Args:
        api_key: The API key to authenticate with

    Returns:
        str: The access token

    Raises:
        AuthenticationError: If authentication fails
        APIError: If the API request fails
    """
    try:
        response = requests.post(
            f"{config.api_url}/accesses/tokens",
            json={"data": {}},
            headers={"x-api-key": api_key},
            timeout=config.get("request_timeout")
        )

        response_json = response.json()
        if response.status_code != 200:
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key", response.status_code, response_json)
            raise APIError(f"Failed to get token: {response_json}", response.status_code, response_json)

        return response_json["data"]["accessToken"]
    except requests.exceptions.Timeout:
        raise APIError("Request timed out while getting access token")
    except requests.exceptions.RequestException as e:
        raise APIError(f"Request failed: {str(e)}")


def post(base_url: str, api_key: str, endpoint: str, data: dict) -> dict:
    """
    Make a POST request to the GAME API.

    Args:
        base_url: The base URL for the API
        api_key: The API key to authenticate with
        endpoint: The API endpoint to call
        data: The data to send in the request

    Returns:
        dict: The API response data

    Raises:
        AuthenticationError: If authentication fails
        APIError: If the API request fails
        ValidationError: If the input data is invalid
    """
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")

    try:
        access_token = get_access_token(api_key)
        
        response = requests.post(
            f"{base_url}/{endpoint}",
            json=data,  # Send data directly without wrapping
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            timeout=config.get("request_timeout")
        )

        # Handle 204 No Content responses
        if response.status_code == 204:
            return {"success": True}

        # Handle empty responses
        if not response.text:
            if response.status_code in [200, 201, 202]:
                return {"success": True}
            raise APIError(f"Empty response from server with status code {response.status_code}")

        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {response.text}")

        if response.status_code not in [200, 201, 202]:
            if response.status_code == 401:
                raise AuthenticationError("Invalid access token", response.status_code, response_json)
            raise APIError(f"API request failed: {response_json}", response.status_code, response_json)

        return response_json.get("data", response_json)  # Handle both wrapped and unwrapped responses
    except requests.exceptions.Timeout:
        raise APIError(f"Request timed out while calling {endpoint}")
    except requests.exceptions.RequestException as e:
        raise APIError(f"Request failed: {str(e)}")


def create_agent(
    base_url: str,
    api_key: str,
    name: str,
    description: str,
    goal: str
) -> dict:
    """
    Create a new agent instance.

    Args:
        base_url: The base URL for the API
        api_key: The API key to authenticate with
        name: Name of the agent
        description: Description of the agent
        goal: Goal of the agent

    Returns:
        dict: The created agent data

    Raises:
        ValidationError: If any required fields are missing
        APIError: If the API request fails
    """
    if not all([name, description, goal]):
        raise ValidationError("name, description, and goal are required")

    data = {
        "data": {  # Wrap in data object as required by API
            "name": name,
            "description": description,
            "goal": goal
        }
    }

    return post(base_url, api_key, "agents", data)


def create_workers(
    base_url: str,
    api_key: str,
    workers: List[Dict[str, Any]]
) -> dict:
    """
    Create workers for the task generator.

    Args:
        base_url: The base URL for the API
        api_key: The API key to authenticate with
        workers: List of worker configurations

    Returns:
        dict: The created workers data

    Raises:
        ValidationError: If the workers list is invalid
        APIError: If the API request fails
    """
    if not isinstance(workers, list):
        raise ValidationError("workers must be a list")

    data = {
        "data": {  # Wrap in data object as required by API
            "workers": workers
        }
    }

    return post(base_url, api_key, "workers", data)
