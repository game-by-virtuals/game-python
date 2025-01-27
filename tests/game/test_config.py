"""Tests for the GAME SDK configuration."""

import unittest
from game_sdk.game.config import Config, config


class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = Config()
        self.assertEqual(config.api_url, "https://api.virtuals.io")
        self.assertEqual(config.version, "v2")
        self.assertEqual(config.default_timeout, 30)

    def test_custom_values(self):
        """Test custom configuration values."""
        config = Config(
            api_url="https://custom.api.com",
            version="v3",
            default_timeout=60
        )
        self.assertEqual(config.api_url, "https://custom.api.com")
        self.assertEqual(config.version, "v3")
        self.assertEqual(config.default_timeout, 60)

    def test_base_url_property(self):
        """Test base_url property."""
        config = Config(api_url="https://custom.api.com")
        self.assertEqual(config.base_url, "https://custom.api.com")

    def test_version_prefix_property(self):
        """Test version_prefix property."""
        config = Config(
            api_url="https://custom.api.com",
            version="v3"
        )
        self.assertEqual(
            config.version_prefix,
            "https://custom.api.com/v3"
        )

    def test_global_config_instance(self):
        """Test global configuration instance."""
        self.assertIsInstance(config, Config)
        self.assertEqual(config.api_url, "https://api.virtuals.io")
        self.assertEqual(config.version, "v2")
        self.assertEqual(config.default_timeout, 30)


if __name__ == '__main__':
    unittest.main()
