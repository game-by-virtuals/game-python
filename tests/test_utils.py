"""
Tests for GAME SDK utility functions.
"""

import pytest
import requests
from unittest.mock import patch, Mock

from game_sdk.game.utils import (
    get_access_token,
    post,
    create_agent,
    create_workers
)
from game_sdk.game.exceptions import (
    APIError,
    AuthenticationError,
    ValidationError
)


def test_get_access_token_success(mock_response):
    """Test successful access token retrieval."""
    mock = mock_response(200, {"data": {"accessToken": "test-token"}})
    
    with patch('requests.post', return_value=mock):
        token = get_access_token("test-key")
        assert token == "test-token"


def test_get_access_token_invalid_key(mock_response):
    """Test authentication failure with invalid API key."""
    mock = mock_response(401, {"error": "Invalid API key"})
    
    with patch('requests.post', return_value=mock):
        with pytest.raises(AuthenticationError) as exc:
            get_access_token("invalid-key")
        assert "Invalid API key" in str(exc.value)


def test_get_access_token_timeout():
    """Test timeout handling in token retrieval."""
    with patch('requests.post', side_effect=requests.exceptions.Timeout):
        with pytest.raises(APIError) as exc:
            get_access_token("test-key")
        assert "timed out" in str(exc.value)


def test_post_success(mock_response):
    """Test successful POST request."""
    token_mock = mock_response(200, {"data": {"accessToken": "test-token"}})
    post_mock = mock_response(200, {"data": {"result": "success"}})
    
    with patch('requests.post') as mock_post:
        mock_post.side_effect = [token_mock, post_mock]
        result = post("https://test.api", "test-key", "test-endpoint", {"test": "data"})
        assert result == {"result": "success"}


def test_post_invalid_data():
    """Test validation of POST request data."""
    with pytest.raises(ValidationError) as exc:
        post("https://test.api", "test-key", "test-endpoint", "invalid-data")
    assert "must be a dictionary" in str(exc.value)


def test_create_agent_success(mock_response):
    """Test successful agent creation."""
    token_mock = mock_response(200, {"data": {"accessToken": "test-token"}})
    agent_mock = mock_response(200, {"data": {"id": "test-agent-id"}})
    
    with patch('requests.post') as mock_post:
        mock_post.side_effect = [token_mock, agent_mock]
        result = create_agent(
            "https://test.api",
            "test-key",
            "Test Agent",
            "Test Description",
            "Test Goal"
        )
        assert result == {"id": "test-agent-id"}


def test_create_agent_missing_fields():
    """Test validation of required agent fields."""
    with pytest.raises(ValidationError) as exc:
        create_agent(
            "https://test.api",
            "test-key",
            "",  # Empty name
            "Test Description",
            "Test Goal"
        )
    assert "required" in str(exc.value)


def test_create_workers_success(mock_response):
    """Test successful worker creation."""
    token_mock = mock_response(200, {"data": {"accessToken": "test-token"}})
    workers_mock = mock_response(200, {"data": {"ids": ["worker1", "worker2"]}})
    
    workers_data = [
        {"description": "Worker 1"},
        {"description": "Worker 2"}
    ]
    
    with patch('requests.post') as mock_post:
        mock_post.side_effect = [token_mock, workers_mock]
        result = create_workers("https://test.api", "test-key", workers_data)
        assert result == {"ids": ["worker1", "worker2"]}


def test_create_workers_invalid_input():
    """Test validation of workers input."""
    with pytest.raises(ValidationError) as exc:
        create_workers("https://test.api", "test-key", "invalid-workers")
    assert "must be a list" in str(exc.value)


def test_create_workers_empty_list():
    """Test validation of empty workers list."""
    with pytest.raises(ValidationError) as exc:
        create_workers("https://test.api", "test-key", [])
    assert "cannot be empty" in str(exc.value)


def test_create_workers_missing_description():
    """Test validation of worker description."""
    with pytest.raises(ValidationError) as exc:
        create_workers("https://test.api", "test-key", [{"name": "Worker"}])
    assert "must have a description" in str(exc.value)
