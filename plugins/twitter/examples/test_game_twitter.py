import os
from twitter_plugin_gamesdk.game_twitter_plugin import GameTwitterPlugin

# Define your options with the necessary credentials
options = {
    "id": "test_game_twitter_plugin",
    "name": "Test GAME Twitter Plugin",
    "description": "An example GAME Twitter Plugin for testing.",
    "credentials": {
        "gameTwitterAccessToken": os.environ.get("GAME_TWITTER_ACCESS_TOKEN")
    },
}

# Initialize the TwitterPlugin with your options
game_twitter_plugin = GameTwitterPlugin(options)

# Test case 1: Post a Tweet
print("\nRunning Test Case 1: Post a Tweet")
post_tweet_fn = game_twitter_plugin.get_function('post_tweet')
post_tweet_fn("Hello world! This is a test tweet from the GAME Twitter Plugin!")
print("Posted tweet!")

# Test case 2: Reply to a Tweet
print("\nRunning Test Case 2: Reply to a Tweet")
reply_tweet_fn = game_twitter_plugin.get_function('reply_tweet')
reply_tweet_fn(tweet_id=1879472470362816626, reply="Hey! This is a test reply!")
print("Replied to tweet!")

# Test case 3: Quote a Tweet
print("\nRunning Test Case 3: Quote a Tweet")
quote_tweet_fn = game_twitter_plugin.get_function('quote_tweet')
quote_tweet_fn(tweet_id=1879472470362816626, quote="Hey! This is a test quote tweet!")
print("Quoted tweet!")

# Test case 4: Search Tweets
print("\nRunning Test Case 4: Search Tweets")
search_tweets_fn = game_twitter_plugin.get_function('search_tweets')
response = search_tweets_fn(query="Python")
print(f"Searched tweets: {response}")

# Test case 5: Get authenticated user
print("\nRunning Test Case 5: Get details of authenticated user")
get_authenticated_user_fn = game_twitter_plugin.get_function('get_authenticated_user')
response = get_authenticated_user_fn()
print(f"Got details of authenticated user: {response}")