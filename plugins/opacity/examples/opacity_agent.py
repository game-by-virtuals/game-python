from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import (
    Function,
    Argument,
    FunctionResult,
    FunctionResultStatus
)
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv
import threading
import time
from opacity_game_sdk.opacity_plugin import OpacityPlugin
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

# Load environment variables
load_dotenv()

# Debug environment variables
print("Environment variables loaded:")
print(f"TWITTER_BEARER_TOKEN: {os.environ.get('TWITTER_BEARER_TOKEN')}")
print(f"GAME_API_KEY: {os.environ.get('GAME_API_KEY')}")
print(f"OPACITY_PROVER_URL: {os.environ.get('OPACITY_PROVER_URL')}")

game_api_key = os.environ.get("GAME_API_KEY")

# Initialize plugins with proper error handling
try:
    twitter_options = {
        "id": "opacity_twitter_plugin",
        "name": "Opacity Twitter Plugin",
        "description": "Twitter Plugin for Opacity verification.",
        "credentials": {
            "bearerToken": os.environ["TWITTER_BEARER_TOKEN"],
            "apiKey": os.environ["TWITTER_API_KEY"],
            "apiSecretKey": os.environ["TWITTER_API_SECRET_KEY"],
            "accessToken": os.environ["TWITTER_ACCESS_TOKEN"],
            "accessTokenSecret": os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
            "clientKey": os.environ["TWITTER_CLIENT_KEY"],
            "clientSecret": os.environ["TWITTER_CLIENT_SECRET"],
        },
    }
    twitter_plugin = TwitterPlugin(twitter_options)
    opacity_plugin = OpacityPlugin()
except Exception as e:
    raise RuntimeError(f"Failed to initialize plugins: {str(e)}")

def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """Simple state management function that returns an empty dict as we don't track state."""
    return {}

def verify_mentioned_results(start_time: str, **kwargs) -> tuple:
    """Function to process Twitter mentions and verify proofs.
    
    1. Get user mentions on Twitter
    2. Extract and verify proofs from original tweets in threads
    3. Reply with verification results
    """
    TWITTER_HANDLE = "opacityverifier"  # Replace with your bot's handle
    
    try:
        # Get user mentions
        get_user_fn = twitter_plugin.get_function('get_user_from_handle')
        user_id = get_user_fn(TWITTER_HANDLE)
        get_user_mentions_fn = twitter_plugin.get_function('get_user_mentions')
        mentions = get_user_mentions_fn(user_id, max_results=10)

        if not mentions:
            return FunctionResultStatus.DONE, "No new mentions to process", {}
        
        processed_count = 0
        verified_count = 0
        
        for mention in mentions:
            tweet_id = mention.get('id')
            
            # Verify the tweet thread
            try:
                status, message, result = opacity_plugin.verify_tweet_thread(tweet_id)
                if status == FunctionResultStatus.DONE:
                    verified_count += 1
            except Exception as e:
                print(f"Error verifying tweet {tweet_id}: {e}")
            
            processed_count += 1
            
        return FunctionResultStatus.DONE, (
            f"Processed {processed_count} mentions, "
            f"verified {verified_count} proofs"
        ), {}

    except Exception as e:
        print(f"Error: {str(e)}")
        return FunctionResultStatus.FAILED, (
            f"Error encountered while processing mentions: {str(e)}"
        ), {}

# Action space with verification capability
action_space = [
    Function(
        fn_name="verify_mentioned_results",
        fn_description="Check Twitter mentions for results to verify",
        args=[
            Argument(
                name="start_time",
                type="string",
                description="Start time for twitter API in YYYY-MM-DDTHH:mm:ssZ format"
            )
        ],
        executable=verify_mentioned_results
    )
]

# Create worker
worker = Worker(
    api_key=game_api_key,
    description="Processing Twitter mentions for Opacity verification requests.",
    instruction="Monitor Twitter mentions and verify AI inference results using Opacity proofs",
    get_state_fn=get_state_fn,
    action_space=action_space
)

def check_mentions():
    """Periodically check for new mentions to process."""
    while True:
        try:
            worker.run("Check Twitter mentions for verification requests")
            print("Waiting for next check cycle...")
            time.sleep(1 * 60)  # Wait 15 minutes between checks
        except Exception as e:
            print(f"Error in check_mentions loop: {e}")
            time.sleep(60)  # Wait a minute before retrying on error

# Create mention checker thread
mention_checker = threading.Thread(target=check_mentions, daemon=True)

if __name__ == "__main__":
    # Start thread
    mention_checker.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")