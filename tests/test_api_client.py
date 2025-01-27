"""
Tests for the GAME SDK API client.

This module contains tests for the GameAPIClient class, including error handling,
retry logic, and HTTP method wrappers.
"""

import pytest
import responses
from requests.exceptions import HTTPError, RequestException
from game_sdk.game.api_client import GameAPIClient
from game_sdk.game.exceptions import APIError, AuthenticationError, ValidationError
from game_sdk.game.config import config


@pytest.fixture
def api_client():
    """Create a test API client instance."""
    return GameAPIClient("test_api_key")


@pytest.fixture
def mock_responses():
    """Set up mock responses for testing."""
    with responses.RequestsMock() as rsps:
        yield rsps


def test_init_with_valid_api_key(api_client):
    """Test client initialization with valid API key."""
    assert api_client.api_key == "test_api_key"
    assert api_client.base_url == config.api_url
    assert api_client.session.headers["Authorization"] == "Bearer test_api_key"
    assert api_client.session.headers["Content-Type"] == "application/json"


def test_init_without_api_key():
    """Test client initialization without API key raises error."""
    with pytest.raises(ValueError, match="API key is required"):
        GameAPIClient("")


def test_get_request_success(api_client, mock_responses):
    """Test successful GET request."""
    expected_response = {"data": "test_data"}
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        json=expected_response,
        status=200
    )

    response = api_client.get("test")
    assert response == expected_response


def test_post_request_success(api_client, mock_responses):
    """Test successful POST request."""
    request_data = {"key": "value"}
    expected_response = {"data": "created"}
    mock_responses.add(
        responses.POST,
        f"{config.api_url}/test",
        json=expected_response,
        status=200
    )

    response = api_client.post("test", request_data)
    assert response == expected_response


def test_put_request_success(api_client, mock_responses):
    """Test successful PUT request."""
    request_data = {"key": "updated_value"}
    expected_response = {"data": "updated"}
    mock_responses.add(
        responses.PUT,
        f"{config.api_url}/test",
        json=expected_response,
        status=200
    )

    response = api_client.put("test", request_data)
    assert response == expected_response


def test_delete_request_success(api_client, mock_responses):
    """Test successful DELETE request."""
    expected_response = {"data": "deleted"}
    mock_responses.add(
        responses.DELETE,
        f"{config.api_url}/test",
        json=expected_response,
        status=200
    )

    response = api_client.delete("test")
    assert response == expected_response


def test_authentication_error(api_client, mock_responses):
    """Test authentication error handling."""
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        json={"error": "Unauthorized"},
        status=401
    )

    with pytest.raises(AuthenticationError, match="Authentication failed"):
        api_client.get("test")


def test_validation_error(api_client, mock_responses):
    """Test validation error handling."""
    mock_responses.add(
        responses.POST,
        f"{config.api_url}/test",
        json={"error": "Invalid data"},
        status=422
    )

    with pytest.raises(ValidationError, match="Invalid request data"):
        api_client.post("test", {})


def test_api_error(api_client, mock_responses):
    """Test general API error handling."""
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        json={"error": "Server error"},
        status=500
    )

    with pytest.raises(tenacity.RetryError):
        api_client.get("test")


def test_network_error(api_client, mock_responses):
    """Test network error handling."""
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        body=RequestException("Network error")
    )

    with pytest.raises(tenacity.RetryError):
        api_client.get("test")


@pytest.mark.parametrize("status_code", [500, 502, 503, 504])
def test_retry_on_server_error(api_client, mock_responses, status_code):
    """Test retry logic on server errors."""
    # First two requests fail, third succeeds
    expected_response = {"data": "success"}
    
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        json={"error": "Server error"},
        status=status_code
    )
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        json={"error": "Server error"},
        status=status_code
    )
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        json=expected_response,
        status=200
    )

    response = api_client.get("test")
    assert response == expected_response
    assert len(mock_responses.calls) == 3  # Verify retry happened


def test_request_with_params(api_client, mock_responses):
    """Test request with query parameters."""
    expected_response = {"data": "filtered"}
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        json=expected_response,
        status=200
    )

    params = {"filter": "value"}
    response = api_client.get("test", params=params)
    assert response == expected_response
    assert "filter=value" in mock_responses.calls[0].request.url


def test_endpoint_path_handling(api_client, mock_responses):
    """Test proper handling of endpoint paths with/without leading slash."""
    expected_response = {"data": "test"}
    
    # Test with leading slash
    mock_responses.add(
        responses.GET,
        f"{config.api_url}/test",
        json=expected_response,
        status=200
    )
    response = api_client.get("/test")
    assert response == expected_response

    # Test without leading slash
    response = api_client.get("test")
    assert response == expected_response
