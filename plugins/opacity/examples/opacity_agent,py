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
import json
import re
from opacity_game_sdk.opacity_plugin import OpacityPlugin
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin


# Load environment variables from .env file
load_dotenv()

# Debug environment variables
print("Environment variables loaded:")
print(f"TWITTER_BEARER_TOKEN: {os.environ.get('TWITTER_BEARER_TOKEN')}")
print(f"GAME_API_KEY: {os.environ.get('GAME_API_KEY')}")
print(f"OPACITY_PROVER_URL: {os.environ.get('OPACITY_PROVER_URL')}")

game_api_key = os.environ.get("GAME_API_KEY")

# Initialize Twitter plugin
twitter_options = {
    "id": "opacity_twitter_plugin",
    "name": "Opacity Twitter Plugin",
    "description": "Twitter Plugin for Opacity verification.",
    "credentials": {
        "bearerToken": os.environ.get("TWITTER_BEARER_TOKEN"),
        "apiKey": os.environ.get("TWITTER_API_KEY"),
        "apiSecretKey": os.environ.get("TWITTER_API_SECRET_KEY"),
        "accessToken": os.environ.get("TWITTER_ACCESS_TOKEN"),
        "accessTokenSecret": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
        "clientKey": os.environ.get("TWITTER_CLIENT_KEY"),
        "clientSecret": os.environ.get("TWITTER_CLIENT_SECRET"),
    },
}

twitter_plugin = TwitterPlugin(twitter_options)
opacity_plugin = OpacityPlugin()


def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """Simple state management function that returns an empty dict as we don't track state."""
    return {}


def extract_proof_from_tweet(tweet_text: str) -> Optional[Dict]:
    """Extract proof ID from tweet text.
    
    Looks for "Proof ID: PROOF_ID" at the end of the tweet.
    """
    try:
        # Look for proof ID at the end of the tweet
        proof_match = re.search(r'Proof ID:\s*(\S+)\s*$', tweet_text)
        if proof_match:
            proof_id = proof_match.group(1)
            return {"proof_id": proof_id}
            
        return None
    except Exception as e:
        print(f"Error extracting proof ID: {e}")
        return None


def get_twitter_user_mentions(username: str) -> Optional[List[Dict]]:
    """Function to get user mentions on twitter using twitter API."""
    try:
        get_user_fn = twitter_plugin.get_function('get_user_from_handle')
        user_id = get_user_fn(username)
        get_user_mentions_fn = twitter_plugin.get_function('get_user_mentions')
        user_mentions = get_user_mentions_fn(user_id, max_results=10)
        return user_mentions
    except Exception as e:
        print(f"Error getting user mentions: {e}")
        return None


def get_original_tweet(tweet_id: str) -> Optional[Dict]:
    """Get the original (root) tweet of a thread.
    
    Follows the chain of referenced tweets up to the first tweet.
    """
    try:
        current_tweet = twitter_plugin.twitter_client.get_tweet(
            tweet_id,
            tweet_fields=['conversation_id', 'referenced_tweets', 'text'],
            expansions=['referenced_tweets.id']
        )

        if not current_tweet.data:
            return None

        # If no referenced tweets, this is the original
        if not hasattr(current_tweet.data, 'referenced_tweets'):
            return {
                'id': tweet_id,
                'text': current_tweet.data['text']
            }

        # Follow the chain of replies to the original tweet
        while True:
            referenced_tweets = current_tweet.data.get('referenced_tweets', [])
            parent_ref = None

            # Look for the 'replied_to' reference
            for ref in referenced_tweets:
                if ref['type'] == 'replied_to':
                    parent_ref = ref
                    break

            # If no parent found, we've reached the original tweet
            if not parent_ref:
                return {
                    'id': current_tweet.data['id'],
                    'text': current_tweet.data['text']
                }

            # Get the parent tweet
            current_tweet = twitter_plugin.twitter_client.get_tweet(
                parent_ref['id'],
                tweet_fields=['conversation_id', 'referenced_tweets', 'text'],
                expansions=['referenced_tweets.id']
            )

            if not current_tweet.data:
                return None

    except Exception as e:
        print(f"Error getting original tweet: {e}")
        return None


def verify_mentioned_results(start_time: str, **kwargs) -> tuple:
    """Function to process Twitter mentions and verify proofs.
    
    1. Get user mentions on Twitter
    2. Extract and verify proofs from original tweets in threads
    3. Reply with verification results
    """
    TWITTER_HANDLE = "opacityverifier"  # Replace with your bot's handle
    
    try:
        mentions = get_twitter_user_mentions(username=TWITTER_HANDLE)
        if not mentions:
            return FunctionResultStatus.DONE, "No new mentions to process", {}
        
        processed_count = 0
        verified_count = 0
        
        for mention in mentions:
            tweet_id = mention.get('id')
            tweet_text = mention.get('text', '')
            
            print(f"Processing mention {tweet_id}: {tweet_text[:100]}...")
            
            # Get the original tweet in the thread
            original_tweet = get_original_tweet(tweet_id)
            if original_tweet:
                print(f"Found original tweet {original_tweet['id']}: {original_tweet['text'][:100]}...")
                
                # Extract proof ID from original tweet
                proof_data = extract_proof_from_tweet(original_tweet['text'])
                if not proof_data:
                    reply_text = (
                        "@{} I couldn't find a proof ID in the original tweet. "
                        "Please ensure the original tweet ends with 'Proof ID: PROOF_ID'"
                    ).format(mention.get('author_id'))
                    twitter_plugin.get_function('reply_tweet')(tweet_id, reply_text)
                    continue
                
                # Verify the proof
                try:
                    is_valid = opacity_plugin.verify_proof({"proof_id": proof_data["proof_id"]})
                    reply_to_verification_tweet(tweet_id, {
                        'valid': is_valid,
                        'original_tweet_id': original_tweet['id'],
                        'proof_id': proof_data["proof_id"]
                    })
                    verified_count += 1
                except Exception as e:
                    print(f"Error verifying proof: {e}")
                    error_text = (
                        "@{} Sorry, I encountered an error while verifying "
                        "the proof. The proof ID might be invalid."
                    ).format(mention.get('author_id'))
                    twitter_plugin.get_function('reply_tweet')(tweet_id, error_text)
            else:
                reply_text = (
                    "@{} I couldn't find the original tweet in this thread. "
                    "Please make sure you're replying in a thread that starts "
                    "with a tweet containing a proof ID."
                ).format(mention.get('author_id'))
                twitter_plugin.get_function('reply_tweet')(tweet_id, reply_text)
            
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


def reply_to_verification_tweet(tweet_id: str, verification_result: dict) -> None:
    """Function to reply to a tweet with the verification result."""
    reply_tweet_fn = twitter_plugin.get_function('reply_tweet')
    
    original_tweet_ref = f"twitter.com/x/status/{verification_result.get('original_tweet_id')}"
    proof_id = verification_result.get('proof_id')
    
    if verification_result['valid']:
        text = (
            f"✅ Verification successful! The AI inference result in the original tweet "
            f"({original_tweet_ref}) has been verified with Proof ID: {proof_id} "
            f"via @opacity_protocol."
        )
    else:
        text = (
            f"❌ Verification failed. The proof (ID: {proof_id}) in the original tweet "
            f"({original_tweet_ref}) is invalid. Please ensure you've provided a "
            f"valid proof ID."
        )
    
    try:
        reply_tweet_fn(tweet_id, text)
    except Exception as e:
        print(f"Error replying to tweet: {e}")


def verify_mentioned_results(start_time: str, **kwargs) -> tuple:
    """Function to process Twitter mentions and verify proofs.
    
    1. Get user mentions on Twitter
    2. Extract and verify proofs from tweets
    3. Reply with verification results
    """
    TWITTER_HANDLE = "opacityverifier"  # Replace with your bot's handle

    try:
        mentions = get_twitter_user_mentions(username=TWITTER_HANDLE)
        if not mentions:
            return FunctionResultStatus.DONE, "No new mentions to process", {}

        processed_count = 0
        verified_count = 0

        for mention in mentions:
            tweet_id = mention.get('id')
            tweet_text = mention.get('text', '')

            # Skip if we've already processed this tweet
            # (you might want to add state management)
            # if is_tweet_processed(tweet_id):
            #     continue

            print(f"Processing tweet {tweet_id}: {tweet_text[:100]}...")

            # Extract proof data from tweet
            proof_data = extract_proof_from_tweet(tweet_text)
            if not proof_data:
                reply_text = (
                    "@{} I couldn't find any proof data in your tweet. "
                    "Please include the proof in JSON format between triple "
                    "backticks or provide a valid proof URL."
                ).format(mention.get('author_id'))
                twitter_plugin.get_function('reply_tweet')(tweet_id, reply_text)
                continue

            # Verify the proof
            try:
                is_valid = opacity_plugin.verify_proof({"proof": proof_data})
                reply_to_verification_tweet(tweet_id, {'valid': is_valid})
                verified_count += 1
            except Exception as e:
                print(f"Error verifying proof: {e}")
                error_text = (
                    "@{} Sorry, I encountered an error while verifying "
                    "your proof. Please ensure the proof data is correctly "
                    "formatted."
                ).format(mention.get('author_id'))
                twitter_plugin.get_function('reply_tweet')(tweet_id, error_text)

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


# Action space with all executables
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
            time.sleep(15 * 60)  # Wait 15 minutes between checks
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