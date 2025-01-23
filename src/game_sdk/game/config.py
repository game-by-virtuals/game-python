"""
Configuration management for the GAME SDK.

This module handles all configuration settings for the SDK, including:
- API endpoints
- Timeouts
- Retry settings
- Environment-specific configurations
"""

import os
from typing import Dict, Any, Optional
from .exceptions import ConfigurationError


class SDKConfig:
    """
    Configuration manager for the GAME SDK.

    This class manages all configuration settings and provides a central place
    to modify SDK behavior.

    Attributes:
        api_base_url (str): Base URL for API calls
        api_version (str): API version to use
        request_timeout (int): Timeout for API requests in seconds
        max_retries (int): Maximum number of retries for failed requests
        retry_delay (int): Delay between retries in seconds
    """

    DEFAULT_CONFIG = {
        "api_base_url": "https://game.virtuals.io",
        "api_version": "v1",
        "request_timeout": 30,
        "max_retries": 3,
        "retry_delay": 1,
    }

    def __init__(self, **kwargs):
        """
        Initialize configuration with optional overrides.

        Args:
            **kwargs: Override default configuration values
        """
        self._config = self.DEFAULT_CONFIG.copy()
        self._config.update(kwargs)

        # Override with environment variables if present
        self._load_env_vars()

    def _load_env_vars(self):
        """Load configuration from environment variables."""
        env_mapping = {
            "GAME_API_BASE_URL": "api_base_url",
            "GAME_API_VERSION": "api_version",
            "GAME_REQUEST_TIMEOUT": "request_timeout",
            "GAME_MAX_RETRIES": "max_retries",
            "GAME_RETRY_DELAY": "retry_delay",
        }

        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert to int for numeric settings
                if config_key in ["request_timeout", "max_retries", "retry_delay"]:
                    try:
                        value = int(value)
                    except ValueError:
                        raise ConfigurationError(
                            f"Invalid value for {env_var}: {value}. Must be an integer."
                        )
                self._config[config_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set a configuration value.

        Args:
            key: Configuration key to set
            value: Value to set

        Raises:
            ConfigurationError: If key is invalid
        """
        if key not in self.DEFAULT_CONFIG:
            raise ConfigurationError(f"Invalid configuration key: {key}")
        self._config[key] = value

    @property
    def api_url(self) -> str:
        """Get the full API URL including version."""
        return f"{self._config['api_base_url']}/{self._config['api_version']}"

    def as_dict(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return self._config.copy()


# Global configuration instance
config = SDKConfig()
