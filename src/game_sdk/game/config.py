"""
Configuration module for the GAME SDK.

This module provides centralized configuration management for the SDK.
"""

from dataclasses import dataclass


@dataclass
class Config:
    """Configuration settings for the GAME SDK.

    Attributes:
        api_url (str): Base URL for API requests
        default_timeout (int): Default timeout for API requests in seconds
    """
    api_url: str = "https://sdk.game.virtuals.io"
    default_timeout: int = 30


# Global configuration instance
config = Config()
