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
from opacity_game_sdk.opacity_plugin import OpacityPlugin
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

class OpacityVerificationWorker:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.game_api_key = os.environ.get("GAME_API_KEY")
        self.opacity_plugin = OpacityPlugin()
        
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
        self.twitter_plugin = TwitterPlugin(twitter_options)
        self.worker = self._create_worker()

    def _get_state(self, function_result: FunctionResult, current_state: dict) -> dict:
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
                current_tweet = self.twitter_plugin.twitter_client.get_tweet(
                    parent_ref['id'],
                    tweet_fields=['conversation_id', 'referenced_tweets', 'text'],
                    expansions=['referenced_tweets.id']
                )
                
                if not current_tweet.data:
                    return None
                    
        except Exception as e:
            print(f"Error getting original tweet: {e}")
            return None

    def _extract_proof_from_tweet(self, tweet_text: str) -> Optional[Dict]:
        """Extract proof ID from tweet text"""
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

    def verify_tweet_thread(self, tweet_id: str) -> tuple:
        """
        Verify a proof from the original tweet in a thread
        """
        try:
            # Get the original tweet
            original_tweet = self._get_original_tweet(tweet_id)
            if not original_tweet:
                return (
                    FunctionResultStatus.FAILED,
                    "Could not find the original tweet in the thread",
                    {}
                )

            # Extract proof ID from original tweet
            proof_data = self._extract_proof_from_tweet(original_tweet['text'])
            if not proof_data:
                return (
                    FunctionResultStatus.FAILED,
                    "No proof ID found in the original tweet",
                    {"original_tweet_id": original_tweet['id']}
                )

            # Verify the proof
            is_valid = self.opacity_plugin.verify_proof({"proof_id": proof_data["proof_id"]})
            
            return (
                FunctionResultStatus.DONE,
                "Proof verification completed",
                {
                    "valid": is_valid,
                    "original_tweet_id": original_tweet['id'],
                    "proof_id": proof_data["proof_id"]
                }
            )
                
        except Exception as e:
            print(f"Error verifying tweet thread: {e}")
            return FunctionResultStatus.FAILED, f"Error: {str(e)}", {}

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
                    fn_description="Verify a proof from the original tweet in a thread",
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