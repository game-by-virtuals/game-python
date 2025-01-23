"""
PyTest configuration and fixtures for GAME SDK tests.
"""

import pytest
from unittest.mock import Mock
from game_sdk.game.config import SDKConfig


@pytest.fixture
def mock_config():
    """Fixture providing a test configuration."""
    return SDKConfig(
        api_base_url="https://test.virtuals.io",
        api_version="test",
        request_timeout=5,
        max_retries=1,
        retry_delay=0,
    )


@pytest.fixture
def mock_response():
    """Fixture providing a mock HTTP response."""
    def _mock_response(status_code=200, json_data=None):
        mock = Mock()
        mock.status_code = status_code
        mock.json.return_value = json_data or {}
        return mock
    return _mock_response
