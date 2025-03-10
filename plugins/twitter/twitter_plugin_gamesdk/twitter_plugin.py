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

import tweepy
import logging
from typing import Dict, Callable, Any, Optional, List, Callable


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
        twitter_client (tweepy.Client): Authenticated Twitter API client
        logger (logging.Logger): Plugin logger

    Raises:
        ValueError: If required Twitter API credentials are missing
    """

    def __init__(self, options: Dict[str, Any]) -> None:
        # Set credentials
        self.id = options.get("id", "twitter_plugin")
        self.name = options.get("name", "Twitter Plugin")
        self.description = options.get(
            "description",
            "A plugin that executes tasks within Twitter, capable of posting, replying, quoting, and liking tweets, and getting metrics.",
        )
        credentials = options.get("credentials")
        if not credentials:
            raise ValueError("Twitter API credentials are required.")
        # Init Tweepy client
        self.twitter_client: tweepy.Client = tweepy.Client(
            bearer_token = credentials.get("bearerToken"),
            consumer_key = credentials.get("apiKey"),
            consumer_secret = credentials.get("apiSecretKey"),
            access_token = credentials.get("accessToken"),
            access_token_secret=credentials.get("accessTokenSecret"),
            return_type = dict
        )
        # Define internal function mappings
        self._functions: Dict[str, Callable[..., Any]] = {
            "get_metrics": self._get_metrics,
            "reply_tweet": self._reply_tweet,
            "post_tweet": self._post_tweet,
            "like_tweet": self._like_tweet,
            "quote_tweet": self._quote_tweet,
            "get_user_from_handle": self._get_user_from_handle,
            "get_user_mentions": self._get_user_mentions
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

    def _get_metrics(self) -> Dict[str, int]:
        """
        Get engagement metrics for the authenticated user.

        Returns:
            Dict[str, int]: User metrics including followers, following, and tweets.

        Raises:
            tweepy.TweepyException: If there's an error accessing the user metrics.
        """
        try:
            user = self.twitter_client.get_me(user_fields=["public_metrics"])
            if not user or not user.get("data", None):
                self.logger.warning("Failed to fetch user metrics.")
                return {}
            public_metrics = user.get("data", {}).get("public_metrics", None)
            return {
                "followers": public_metrics.get("followers_count", 0),
                "following": public_metrics.get("following_count", 0),
                "tweets": public_metrics.get("tweet_count", 0),
            }
        except tweepy.TweepyException as e:
            self.logger.error(f"Failed to fetch metrics: {e}")
            return {}

    def _reply_tweet(self, tweet_id: int, reply: str, media_ids: Optional[str] = None) -> None:
        """
        Reply to a specific tweet.

        Args:
            tweet_id (int): ID of the tweet to reply to.
            reply (str): Content of the reply.

        Raises:
            tweepy.TweepyException: If there's an error posting the reply.
        """
        try:
            if media_ids and len(media_ids) > 4:
                raise ValueError("media_ids cannot contain more than 4 items.")
            self.twitter_client.create_tweet(in_reply_to_tweet_id=tweet_id, text=reply)
            self.logger.info(f"Successfully replied to tweet {tweet_id}.")
        except tweepy.TweepyException as e:
            self.logger.error(f"Failed to reply to tweet {tweet_id}: {e}")

    def _post_tweet(self, tweet: str, media_ids: Optional[str] = None) -> Dict[str, Any]:
        """
        Post a new tweet.

        Args:
            tweet (str): Content of the tweet.

        Returns:
            Dict[str, Any]: Details of the posted tweet.

        Raises:
            tweepy.TweepyException: If there's an error posting the tweet.
        """
        try:
            if media_ids and len(media_ids) > 4:
                raise ValueError("media_ids cannot contain more than 4 items.")
            self.twitter_client.create_tweet(text=tweet)
            self.logger.info("Tweet posted successfully.")
        except tweepy.TweepyException as e:
            self.logger.error(f"Failed to post tweet: {e}")

    def _like_tweet(self, tweet_id: int) -> None:
        """
        Like a specific tweet.

        Args:
            tweet_id (int): ID of the tweet to like.

        Raises:
            tweepy.TweepyException: If there's an error liking the tweet.
        """
        try:
            self.twitter_client.like(tweet_id)
            self.logger.info(f"Tweet {tweet_id} liked successfully.")
        except tweepy.TweepyException as e:
            self.logger.error(f"Failed to like tweet {tweet_id}: {e}")

    def _quote_tweet(self, tweet_id: int, quote: str, media_ids: Optional[str] = None) -> None:
        """
        Quote a specific tweet with additional text.

        Args:
            tweet_id (int): ID of the tweet to quote.
            quote (str): Text to add to the quote.

        Raises:
            tweepy.TweepyException: If there's an error posting the quote tweet.
        """
        try:
            self.twitter_client.create_tweet(quote_tweet_id=tweet_id, text=quote, media_ids=media_ids)
            self.logger.info(f"Successfully quoted tweet {tweet_id}.")
        except tweepy.TweepyException as e:
            self.logger.error(f"Failed to quote tweet {tweet_id}: {e}")

    def _get_user_from_handle(self, username) -> Optional[int]:
        """
        Extract the Twitter user ID from a profile URL using TwitterClient.
        """
        try:
            # Fetch user information using the Twitter client
            user = self.twitter_client.get_user(username=username)
            return user['data']['id']
        except tweepy.TweepyException as e:
            self.logger.warning(f"Error fetching user data: {e}")
            return None

    def _get_user_mentions(self, user_id: int, end_time=None, max_results: int = 10) -> Optional[List[Dict]]:
        """
        Fetch mentions for a specific user
        """
        try:
            # Fetch mentions using the Twitter client
            mentions = self.twitter_client.get_users_mentions(
                id = user_id, 
                end_time = end_time, 
                max_results = max_results,
                tweet_fields = ["id", "created_at", "text"],
                expansions = ["attachments.media_keys"],
                media_fields = ["url"]
            )
            if not mentions['data']:
                return None
            # Create a mapping of media keys to media URLs
            media_dict = {}
            media_list = mentions.get('includes', {}).get('media', [])
            if media_list:
                for media in media_list:
                    if 'url' in media:
                        media_dict[media['media_key']] = media['url']
            result = []
            for mention in mentions['data']:
                media_keys = mention.get('attachments', {}).get('media_keys', [])
                # Get image urls from media_dict
                media_urls = []
                for media_key in media_keys:
                    if media_key in media_dict:
                        media_urls.append(media_dict[media_key])
                # Append tweet text and media URLs to the result
                result.append({
                    "id": mention["id"],
                    "text": mention["text"],
                    "media_urls": media_urls
                })
            return result
        except tweepy.TweepyException as e:
            self.logger.warning(f"Error fetching user mentions: {e}")
            return []
        
    def _get_tweets(self, username: str, max_results: int = 100) -> Optional[List[Dict]]:
        """
        Fetch tweets for a specific user
        """
        try:
            tweets = self.twitter_client.get_users_tweets(username, max_results=max_results)
            return tweets
        except tweepy.TweepyException as e:
            self.logger.warning(f"Error fetching tweets: {e}")
            return []
