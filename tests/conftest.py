"""Common test fixtures and configuration."""
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_api_key():
    return "test-api-key-12345"

@pytest.fixture
def mock_response():
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {"data": []}
    return mock

@pytest.fixture
def mock_requests(monkeypatch, mock_response):
    """Mock requests to avoid actual API calls during tests."""
    mock_get = Mock(return_value=mock_response)
    mock_post = Mock(return_value=mock_response)
    
    class MockRequests:
        get = mock_get
        post = mock_post
    
    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr("requests.post", mock_post)
    
    return MockRequests()
