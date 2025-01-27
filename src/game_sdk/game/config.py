"""
Configuration module for the GAME SDK.

This module provides centralized configuration management for the SDK.
"""

from dataclasses import dataclass


@dataclass
class Config:
    """Configuration class for the GAME SDK."""
    api_url: str = "https://api.virtuals.io"
    version: str = "v2"
    default_timeout: int = 30

    @property
    def base_url(self) -> str:
        """Get the base URL for API calls."""
        return self.api_url

    @property
    def version_prefix(self) -> str:
        """Get the versioned API prefix."""
        return f"{self.api_url}/{self.version}"


# Global configuration instance
config = Config()
