"""
Twitter Plugin for the GAME SDK.

This plugin provides a wrapper around the Twitter API using tweepy, enabling
GAME SDK agents to interact with Twitter programmatically. It supports common
Twitter operations like posting tweets, replying, quoting, and getting metrics.

Example:
    ```python
    options = {
        "id": "twitter_agent",
        "name": "Twitter Bot",
        "description": "A Twitter bot that posts updates",
        "credentials": {
            "bearerToken": "your_bearer_token",
            "apiKey": "your_api_key",
            "apiSecretKey": "your_api_secret",
            "accessToken": "your_access_token",
            "accessTokenSecret": "your_access_token_secret"
        }
    }
    
    twitter_plugin = TwitterPlugin(options)
    post_tweet_fn = twitter_plugin.get_function('post_tweet')
    post_tweet_fn("Hello, World!")
    ```
"""

import logging
from typing import Dict, Any
from virtuals_tweepy import Client, TweepyException

class TwitterPlugin:
    """
    A plugin for interacting with Twitter through the GAME SDK.

    This class provides a set of functions for common Twitter operations,
    wrapped in a format compatible with the GAME SDK's plugin system.

    Args:
        options (Dict[str, Any]): Configuration options including:
            - id (str): Unique identifier for the plugin instance
            - name (str): Display name for the plugin
            - description (str): Plugin description
            - credentials (Dict[str, str]): Twitter API credentials

    Attributes:
        id (str): Plugin identifier
        name (str): Plugin name
        description (str): Plugin description
        twitter_client (virtuals_tweepy.Client): Authenticated Twitter API client
        logger (logging.Logger): Plugin logger

    Raises:
        ValueError: If required Twitter API credentials are missing
    """

    def __init__(self, options: Dict[str, Any]) -> None:
        # Set credentials
        self.base_url = options.get("base_url", "https://twitter.game.virtuals.io") + '/tweets'
        credentials = options.get("credentials")
        if not credentials:
            raise ValueError("Twitter API credentials are required.")

        # Capture token for internal use
        self.game_twitter_access_token = credentials.get("game_twitter_access_token")

        # Auth gate: require EITHER gameTwitterAccessToken OR full credential set
        has_api_credentials = all(
            credentials.get(key) for key in ["api_key", "api_key_secret", "access_token", "access_token_secret"]
        )

        if not self.game_twitter_access_token and not has_api_credentials:
            raise ValueError(
                "Missing valid authentication. Provide either a 'game_twitter_access_token' or all required Twitter API credentials."
            )

        # Init Tweepy client
        self.twitter_client: Client = Client(
            consumer_key = credentials.get("api_key"),
            consumer_secret = credentials.get("api_key_secret"),
            access_token = credentials.get("access_token"),
            access_token_secret=credentials.get("access_token_secret"),
            return_type = dict,
            game_twitter_access_token = credentials.get("game_twitter_access_token"),
        )
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger: logging.Logger = logging.getLogger(__name__)

        self._check_authentication()

    def _check_authentication(self) -> None:
        """
        Check if the credentials provided are valid by calling the /me endpoint or fetching user info.
        """
        try:
            user = self.twitter_client.get_me(user_fields=["public_metrics"]).get('data')
            self.logger.info(f"Authenticated as: {user.get('name')} (@{user.get('username')})")
        except TweepyException as e:
            self.logger.error(f"Authentication failed: {e}")
            raise ValueError("Invalid Twitter credentials or failed authentication.")
