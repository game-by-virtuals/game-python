"""
Utility functions for the GAME SDK.

This module provides core utility functions for interacting with the GAME API,
including authentication, agent creation, and worker management.

The module handles:
- API authentication and token management
- HTTP request handling with proper error handling
- Agent and worker creation
- Response parsing and validation

Example:
    # Create an agent
    agent_id = create_agent(
        base_url="https://api.virtuals.io",
        api_key="your_api_key",
        name="My Agent",
        description="A helpful agent",
        goal="To assist users"
    )
"""

import json
import requests
from typing import Dict, Any, Optional, List
from requests.exceptions import ConnectionError, Timeout, JSONDecodeError
from game_sdk.game.exceptions import APIError, AuthenticationError, ValidationError


def post(
    base_url: str,
    api_key: str,
    endpoint: str,
    data: Dict[str, Any] = None,
    params: Dict[str, Any] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """Make a POST request to the GAME API.

    This function handles all POST requests to the API, including proper
    error handling, response validation, and authentication.

    Args:
        base_url (str): Base URL for the API
        api_key (str): API key for authentication
        endpoint (str): API endpoint to call
        data (Dict[str, Any], optional): Request payload
        params (Dict[str, Any], optional): URL parameters
        timeout (int, optional): Request timeout in seconds. Defaults to 30.

    Returns:
        Dict[str, Any]: Parsed response data from the API

    Raises:
        AuthenticationError: If API key is invalid
        ValidationError: If request data is invalid
        APIError: For other API-related errors including network issues
        
    Example:
        response = post(
            base_url="https://api.virtuals.io",
            api_key="your_api_key",
            endpoint="/v2/agents",
            data={"name": "My Agent"}
        )
    """
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=data,
            params=params,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout
        )

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 400:
            raise ValidationError(response.json().get("error", {}).get("message", "Invalid request"))
        elif response.status_code == 429:
            raise APIError("Rate limit exceeded", status_code=429)
        elif response.status_code >= 500:
            raise APIError("Server error", status_code=response.status_code)
        elif response.status_code == 204:
            # Handle no content response
            return {"id": data.get("name", "default_id")}

        try:
            if response.text:
                return response.json().get("data", {})
            return {}
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response")

    except requests.exceptions.ConnectionError as e:
        raise APIError(f"Connection failed: {str(e)}")
    except requests.exceptions.Timeout as e:
        raise APIError(f"Connection timeout: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise APIError(f"Request failed: {str(e)}")


def create_agent(
    base_url: str,
    api_key: str,
    name: str,
    description: str,
    goal: str
) -> str:
    """Create a new agent instance.

    This function creates a new agent with the specified parameters.
    An agent can be either a standalone agent or one with a task generator.

    Args:
        base_url (str): Base URL for the API
        api_key (str): API key for authentication
        name (str): Name of the agent
        description (str): Description of the agent's capabilities
        goal (str): The agent's primary goal or purpose

    Returns:
        str: ID of the created agent

    Raises:
        ValidationError: If name is empty or invalid
        APIError: If agent creation fails
        AuthenticationError: If API key is invalid

    Example:
        agent_id = create_agent(
            base_url="https://api.virtuals.io",
            api_key="your_api_key",
            name="Support Agent",
            description="Helps users with support requests",
            goal="To provide excellent customer support"
        )
    """
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Name cannot be empty")

    create_agent_response = post(
        base_url,
        api_key,
        endpoint="/v2/agents",
        data={
            "name": name,
            "description": description,
            "goal": goal,
        }
    )

    agent_id = create_agent_response.get("id")
    if not agent_id:
        raise APIError("Failed to create agent: missing id in response")

    return agent_id


def create_workers(
    base_url: str,
    api_key: str,
    workers: List[Any]
) -> str:
    """Create worker instances for an agent.

    This function creates one or more workers that can be assigned tasks
    by the agent. Each worker has its own description and action space.

    Args:
        base_url (str): Base URL for the API
        api_key (str): API key for authentication
        workers (List[Any]): List of worker configurations

    Returns:
        str: ID of the created worker map

    Raises:
        APIError: If worker creation fails
        ValidationError: If worker configuration is invalid
        AuthenticationError: If API key is invalid

    Example:
        worker_map_id = create_workers(
            base_url="https://api.virtuals.io",
            api_key="your_api_key",
            workers=[worker_config1, worker_config2]
        )
    """
    locations = []
    for worker in workers:
        location = {
            "name": worker.id,
            "description": worker.worker_description,
            "functions": [
                {
                    "name": fn.fn_name,
                    "description": fn.fn_description,
                    "args": fn.args
                }
                for fn in worker.functions
            ]
        }
        locations.append(location)

    response = post(
        base_url,
        api_key,
        endpoint="/v2/maps",
        data={"locations": locations}
    )

    return response["id"]


def validate_response(response: Dict[str, Any]) -> None:
    """Validate API response format.
    
    Args:
        response (Dict[str, Any]): Response from API
        
    Raises:
        ValueError: If response is invalid
    """
    if response is None:
        raise ValueError("Response cannot be None")
    if not isinstance(response, dict):
        raise ValueError("Response must be a dictionary")
    if not response:
        raise ValueError("Response cannot be empty")
    if "status" in response and response["status"] == "error":
        raise ValueError("Response indicates error status")
    if "data" in response and response["data"] is None:
        raise ValueError("Response data cannot be None")


def format_endpoint(endpoint: str) -> str:
    """Format API endpoint.
    
    Args:
        endpoint (str): Endpoint to format
        
    Returns:
        str: Formatted endpoint
    """
    endpoint = endpoint.strip("/")
    return f"/{endpoint}" if endpoint else "/"


def merge_params(
    base_params: Optional[Dict[str, Any]] = None,
    additional_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Merge two parameter dictionaries.
    
    Args:
        base_params (Optional[Dict[str, Any]], optional): Base parameters. Defaults to None.
        additional_params (Optional[Dict[str, Any]], optional): Additional parameters. Defaults to None.
        
    Returns:
        Dict[str, Any]: Merged parameters
    """
    params = base_params.copy() if base_params else {}
    if additional_params:
        params.update(additional_params)
    return params


def parse_api_error(error_response: Dict[str, Any]) -> str:
    """Parse error message from API response.
    
    Args:
        error_response (Dict[str, Any]): Error response from API
        
    Returns:
        str: Parsed error message
    """
    if "error" in error_response:
        error = error_response["error"]
        if isinstance(error, dict):
            return error.get("message") or error.get("detail", "Unknown error")
        return str(error)
    elif "message" in error_response:
        return str(error_response["message"])
    return "Unknown error"
