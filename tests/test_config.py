"""
Tests for the GAME SDK configuration system.
"""

import os
import pytest
from game_sdk.game.config import SDKConfig
from game_sdk.game.exceptions import ConfigurationError


def test_default_config():
    """Test that default configuration is loaded correctly."""
    config = SDKConfig()
    assert config.get("api_base_url") == "https://game.virtuals.io"
    assert config.get("api_version") == "v1"
    assert config.get("request_timeout") == 30


def test_config_override():
    """Test that configuration can be overridden."""
    config = SDKConfig(api_base_url="https://test.example.com")
    assert config.get("api_base_url") == "https://test.example.com"
    # Other values should remain default
    assert config.get("api_version") == "v1"


def test_env_var_override(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("GAME_API_BASE_URL", "https://env.example.com")
    monkeypatch.setenv("GAME_REQUEST_TIMEOUT", "60")
    
    config = SDKConfig()
    assert config.get("api_base_url") == "https://env.example.com"
    assert config.get("request_timeout") == 60


def test_invalid_config_key():
    """Test that setting invalid configuration keys raises an error."""
    config = SDKConfig()
    with pytest.raises(ConfigurationError):
        config.set("invalid_key", "value")


def test_api_url_property():
    """Test the api_url property combines base URL and version correctly."""
    config = SDKConfig(
        api_base_url="https://test.example.com",
        api_version="v2"
    )
    assert config.api_url == "https://test.example.com/v2"
