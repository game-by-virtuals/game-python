"""
GAME Twitter Plugin for the GAME SDK.

This plugin provides a wrapper around the Twitter API using a GAME twitter endpoint (maintained by GAME devs), 
enabling GAME SDK agents to interact with Twitter programmatically using the access token from 
game_twitter_auth.py. It supports common Twitter operations like posting tweets, replying and quoting.

Example:
    ```python
    options = {
        "id": "twitter_agent",
        "name": "Twitter Bot",
        "description": "A Twitter bot that posts updates",
        "credentials": {
            "gameTwitterAccessToken": "your_access_token"
        }
    }
    
    game_twitter_plugin = GameTwitterPlugin(options)
    post_tweet_fn = game_twitter_plugin.get_function('post_tweet')
    post_tweet_fn("Hello, World!")
    ```
"""

import requests
from typing import Optional, Dict, Any, Callable, List
import os
import logging


class GameTwitterPlugin:
    """
    Used to make Twitter API requests using GAME access token
    """
    def __init__(self, options: Dict[str, Any]) -> None:
        """
        Initialize the client with an access token and base URL.
        """
        # Set credentials
        self.id = options.get("id", "game_twitter_plugin")
        self.name = options.get("name", "GAME Twitter Plugin")
        self.description = options.get(
            "description",
            "A plugin that executes tasks within Twitter, capable of posting, replying, quoting, and liking tweets, and getting metrics.",
        )
        credentials = options.get("credentials")
        if not credentials:
            raise ValueError("Twitter API credentials are required.")
        # Set GAME Twitter configs, e.g. base URL
        self.base_url = "https://twitter.game.virtuals.io/tweets"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": credentials.get("gameTwitterAccessToken", None),
        }
        # Define internal function mappings
        self._functions: Dict[str, Callable[..., Any]] = {
            "reply_tweet": self._reply_tweet,
            "post_tweet": self._post_tweet,
            "like_tweet": self._like_tweet,
            "quote_tweet": self._quote_tweet,
            "search_tweets": self._search_tweets,
            "get_authenticated_user": self._get_authenticated_user,
            "mentions": self._mentions,
            "followers": self._followers,
            "following": self._following
        }
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger: logging.Logger = logging.getLogger(__name__)

    @property
    def available_functions(self) -> List[str]:
        """
        Get a list of all available Twitter functions.

        Returns:
            List[str]: Names of all available functions in this plugin.
        """
        return list(self._functions.keys())

    def get_function(self, fn_name: str) -> Callable:
        """
        Retrieve a specific Twitter function by name.

        Args:
            fn_name (str): Name of the function to retrieve.

        Returns:
            Callable: The requested function.

        Raises:
            ValueError: If the requested function name is not found.

        Example:
            ```python
            post_tweet = twitter_plugin.get_function('post_tweet')
            post_tweet("Hello from GAME SDK!")
            ```
        """
        if fn_name not in self._functions:
            raise ValueError(
                f"Function '{fn_name}' not found. Available functions: {', '.join(self.available_functions)}"
            )
        return self._functions[fn_name]

    def _fetch_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None):
        """
        Generic method to handle API requests.
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=data)

        if response.status_code not in [200, 201]:
            raise Exception(f"Error {response.status_code}: {response.text}")

        return response.json()

    def _post_tweet(self, tweet: str, media_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Post a tweet with optional media.
        """
        if media_ids and len(media_ids) > 4:
            raise ValueError("media_ids cannot contain more than 4 items.")
        payload = {"content": tweet}
        if media_ids:
            payload["mediaIds"] = media_ids
        return self._fetch_api("/post", "POST", data=payload)

    def _search_tweets(self, query: str) -> Dict[str, Any]:
        """
        Search for tweets.
        """
        return self._fetch_api(f"/search?query={requests.utils.quote(query)}", "GET")

    def _reply_tweet(self, tweet_id: int, reply: str, media_ids: Optional[str] = None) -> None:
        """
        Reply to a tweet.
        """
        if media_ids and len(media_ids) > 4:
            raise ValueError("media_ids cannot contain more than 4 items.")
        payload = {"content": reply}
        if media_ids:
            payload["mediaIds"] = media_ids
        return self._fetch_api(f"/reply/{tweet_id}", "POST", data=payload)

    def _like_tweet(self, tweet_id: int) -> None:
        """
        Like a tweet.
        """
        return self._fetch_api(f"/like/{tweet_id}", "POST")

    def _quote_tweet(self, tweet_id: int, quote: str, media_ids: Optional[str] = None) -> None:
        """
        Quote a tweet.
        """
        if media_ids and len(media_ids) > 4:
            raise ValueError("media_ids cannot contain more than 4 items.")
        payload = {"content": quote}
        if media_ids:
            payload["mediaIds"] = media_ids
        return self._fetch_api(f"/quote/{tweet_id}", "POST", data=payload)

    def _get_authenticated_user(self) -> Dict[str, Any]:
        """
        Get details of the authenticated user.
        """
        return self._fetch_api("/me", "GET")

    def _mentions(self, pagination_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get mentions of the authenticated user.
        """
        endpoint = "/mentions"
        if pagination_token:
            endpoint += f"?paginationToken={paginationToken}"
        return self._fetch_api(endpoint, "GET")

    def _followers(self, pagination_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get followers of the authenticated user.
        """
        endpoint = "/followers"
        if pagination_token:
            endpoint += f"?paginationToken={paginationToken}"
        return self._fetch_api(endpoint, "GET")

    def _following(self, pagination_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of users whom the authenticated user is following.
        """
        endpoint = "/following"
        if pagination_token:
            endpoint += f"?paginationToken={paginationToken}"
        return self._fetch_api(endpoint, "GET")
    
    def upload_media(self, media: bytes) -> str:
        """
        Uploads media (e.g. image, video) to X and returns the media ID.
        """
        response = requests.post(
            url = f"{self.base_url}/media",
            headers = {k: v for k, v in self.headers.items() if k != "Content-Type"},
            files = {"file": media}
        )
        return response.json().get("mediaId")