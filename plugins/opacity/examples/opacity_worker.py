from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import (
    Function,
    Argument,
    FunctionResult,
    FunctionResultStatus
)
from typing import Dict, Optional
import os
from dotenv import load_dotenv
import re
import requests
from opacity_game_sdk.opacity_plugin import OpacityPlugin
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin


class OpacityVerificationWorker:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.game_api_key = os.environ.get("GAME_API_KEY")

        if not self.game_api_key:
            raise ValueError("GAME_API_KEY not found in environment variables")

        # Required Twitter credentials
        required_twitter_creds = [
            "TWITTER_BEARER_TOKEN",
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET_KEY",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET",
            "TWITTER_CLIENT_KEY",
            "TWITTER_CLIENT_SECRET"
        ]

        # Validate all Twitter credentials exist
        missing_creds = [
            cred for cred in required_twitter_creds
            if not os.environ.get(cred)
        ]
        if missing_creds:
            raise ValueError(
                f"Missing Twitter credentials: {', '.join(missing_creds)}"
            )

        self.opacity_plugin = OpacityPlugin()

        # Initialize Twitter plugin with error handling
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
            self.twitter_plugin = TwitterPlugin(twitter_options)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize Twitter plugin: {str(e)}")

        self.worker = self._create_worker()

    def _get_state(self, function_result: FunctionResult,
                   current_state: dict) -> dict:
        """Simple state management"""
        return {}

    def _get_original_tweet(self, tweet_id: str) -> Optional[Dict]:
        """Get the original (root) tweet of a thread"""
        try:
            current_tweet = self.twitter_plugin.twitter_client.get_tweet(
                tweet_id,
                tweet_fields=['conversation_id', 'referenced_tweets', 'text'],
                expansions=['referenced_tweets.id']
            )

            if not current_tweet or not current_tweet.data:
                raise ValueError(f"Tweet with ID {tweet_id} not found")

            # If no referenced tweets, this is the original
            referenced_tweets = getattr(
                current_tweet.data, 'referenced_tweets', None
            )
            if not referenced_tweets:
                return {
                    'id': str(current_tweet.data.id),  # Ensure ID is string
                    'text': current_tweet.data.text
                }

            # Follow the chain of replies to the original tweet
            while True:
                referenced_tweets = current_tweet.data.get('referenced_tweets', [])
                parent_ref = None

                # Look for the 'replied_to' reference
                for ref in referenced_tweets:
                    # Access as attribute instead of dict
                    if ref.type == 'replied_to':
                        parent_ref = ref
                        break

                # If no parent found, we've reached the original tweet
                if not parent_ref:
                    return {
                        'id': str(current_tweet.data.id),  # Ensure ID is string
                        'text': current_tweet.data.text
                    }

                # Get the parent tweet
                current_tweet = self.twitter_plugin.twitter_client.get_tweet(
                    str(parent_ref.id),  # Ensure ID is string
                    tweet_fields=['conversation_id', 'referenced_tweets', 'text'],
                    expansions=['referenced_tweets.id']
                )

                if not current_tweet or not current_tweet.data:
                    return None

        except Exception as e:
            error_msg = str(e).lower()
            if "unauthorized" in error_msg:
                raise RuntimeError(
                    "Twitter API authentication failed. "
                    "Please check your credentials."
                )
            elif "not found" in error_msg:
                raise ValueError(f"Tweet with ID {tweet_id} does not exist")
            elif "forbidden" in error_msg:
                raise RuntimeError(
                    "Twitter API access forbidden. Please check API permissions."
                )
            else:
                raise RuntimeError(f"Error accessing tweet: {str(e)}")

    def _extract_proof_from_tweet(self, tweet_text: str) -> Optional[Dict]:
        """Extract proof ID from tweet text"""
        try:
            # Debug log
            print(f"Attempting to extract proof from tweet text: {tweet_text}")

            # Look for proof ID at the end of the tweet
            proof_match = re.search(
                r'Proof ID:\s*(\S+)\s*$',
                tweet_text,
                re.IGNORECASE
            )
            if proof_match:
                proof_id = proof_match.group(1)
                print(f"Found proof ID: {proof_id}")  # Debug log
                return {"proof_id": proof_id}

            print("No proof ID found in tweet text")  # Debug log
            return None
        except Exception as e:
            print(f"Error extracting proof ID: {e}")
            return None

    def verify_tweet_thread(self, tweet_id: str) -> tuple:
        """Verify a proof from the original tweet in a thread"""
        try:
            # Input validation
            if not tweet_id or not isinstance(tweet_id, str):
                return (
                    FunctionResultStatus.FAILED,
                    "Invalid tweet ID provided",
                    {}
                )

            # Get the original tweet
            try:
                original_tweet = self._get_original_tweet(tweet_id)
                if not original_tweet:
                    return (
                        FunctionResultStatus.FAILED,
                        "Could not retrieve original tweet",
                        {}
                    )
                # Debug log
                print(f"Retrieved original tweet: {original_tweet}")

            except Exception as e:
                return (
                    FunctionResultStatus.FAILED,
                    f"Error retrieving tweet: {str(e)}",
                    {}
                )

            # Extract proof ID from original tweet
            try:
                proof_data = self._extract_proof_from_tweet(original_tweet['text'])
                if not proof_data:
                    return (
                        FunctionResultStatus.FAILED,
                        "No proof ID found in the original tweet",
                        {"original_tweet_id": original_tweet['id']}
                    )
                print(f"Extracted proof data: {proof_data}")  # Debug log

            except Exception as e:
                return (
                    FunctionResultStatus.FAILED,
                    f"Error extracting proof data: {str(e)}",
                    {
                        "original_tweet_id": (
                            original_tweet['id'] if original_tweet else None
                        )
                    }
                )

            # Verify the proof
            try:
                proof_id = proof_data["proof_id"]
                # Debug log
                print(f"Attempting to verify proof ID: {proof_id}")

                # First, fetch the proof data using the ID
                try:
                    proof_response = requests.get(
                        f"{self.opacity_plugin.prover_url}/api/logs/{proof_id}"
                    )
                    if not proof_response.ok:
                        raise Exception(
                            f"Failed to fetch proof data: {proof_response.text}"
                        )
                    proof = proof_response.json()
                except Exception as e:
                    raise Exception(f"Error fetching proof data: {str(e)}")

                # Send the proof data directly
                verification_result = self.opacity_plugin.verify_proof(
                    {"proof": proof}
                )

                return (
                    FunctionResultStatus.DONE,
                    "Proof verification completed",
                    {
                        "valid": verification_result,
                        "original_tweet_id": original_tweet['id'],
                        "proof_id": proof_id
                    }
                )
            except Exception as e:
                error_msg = f"Error during proof verification: {str(e)}"
                # Debug log
                print(f"Verification error details: {error_msg}")
                return (
                    FunctionResultStatus.FAILED,
                    error_msg,
                    {
                        "original_tweet_id": original_tweet['id'],
                        "proof_id": proof_data["proof_id"]
                    }
                )

        except Exception as e:
            error_msg = f"Unexpected error during verification: {str(e)}"
            print(error_msg)
            return FunctionResultStatus.FAILED, error_msg, {}

    def _create_worker(self) -> Worker:
        """Create worker with thread verification capability"""
        return Worker(
            api_key=self.game_api_key,
            description="Worker for verifying AI inference proofs using Opacity",
            instruction="Verify proofs in Twitter threads",
            get_state_fn=self._get_state,
            action_space=[
                Function(
                    fn_name="verify_tweet_thread",
                    fn_description=(
                        "Verify a proof from the original tweet in a thread"
                    ),
                    args=[
                        Argument(
                            name="tweet_id",
                            type="string",
                            description="ID of any tweet in the thread to verify"
                        )
                    ],
                    executable=self.verify_tweet_thread
                )
            ]
        )

    def run(self, tweet_id: str):
        """Run the worker on a single tweet thread"""
        self.worker.run(f"Verify tweet thread: {tweet_id}")


def main():
    # Example usage
    worker = OpacityVerificationWorker()

    # Test with a real tweet ID
    test_tweet_id = "1885493193614950476"  # Replace with actual tweet ID
    worker.run(test_tweet_id)


if __name__ == "__main__":
    main()