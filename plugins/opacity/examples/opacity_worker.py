from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import (
    Function,
    Argument,
    FunctionResult,
    FunctionResultStatus
)
from typing import Dict, Optional, Tuple
import os
from dotenv import load_dotenv
import re
import requests
from opacity_game_sdk.opacity_plugin import OpacityPlugin
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
import time
from pathlib import Path
import sys

class OpacityVerificationWorker:
    def __init__(self):
        self._initialize_environment()
        self._initialize_plugins()
        self._initialize_verified_agents()
        self.worker = self._create_worker()

    def _initialize_environment(self):
        """Initialize and validate environment variables."""
        load_dotenv()
        self.game_api_key = os.environ.get("GAME_API_KEY")

        if not self.game_api_key:
            raise ValueError("GAME_API_KEY not found in environment variables")

        required_twitter_creds = [
            "TWITTER_BEARER_TOKEN",
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET_KEY",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET",
            "TWITTER_CLIENT_KEY",
            "TWITTER_CLIENT_SECRET"
        ]

        missing_creds = [
            cred for cred in required_twitter_creds
            if not os.environ.get(cred)
        ]
        if missing_creds:
            raise ValueError(
                f"Missing Twitter credentials: {', '.join(missing_creds)}"
            )

    def _initialize_plugins(self):
        """Initialize Opacity and Twitter plugins."""
        self.opacity_plugin = OpacityPlugin()

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

    def _initialize_verified_agents(self):
        """Initialize tracking of verified agents."""
        self.verified_agents_file = "verified_agents.txt"
        self.verified_tweets_file = "verified_tweets.txt"
        self.verified_agents = self._load_verified_agents()
        self.verified_tweets = self._load_verified_tweets()

    def _get_state(
        self,
        function_result: FunctionResult,
        current_state: dict
    ) -> dict:
        """Simple state management."""
        return {}

    def _load_verified_agents(self) -> set:
        """Load previously verified agents from file."""
        try:
            if os.path.exists(self.verified_agents_file):
                with open(self.verified_agents_file, 'r') as f:
                    return set(line.strip() for line in f)
            return set()
        except Exception as e:
            print(f"Error loading verified agents: {e}")
            return set()

    def _save_verified_agent(self, agent_id: str) -> bool:
        """Save newly verified agent to file. Returns True if agent was newly added."""
        try:
            if agent_id in self.verified_agents:
                return False
            with open(self.verified_agents_file, 'a') as f:
                f.write(f"{agent_id}\n")
            self.verified_agents.add(agent_id)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save verified agent: {e}")
            return False
        
    def _load_verified_tweets(self) -> set:
        """Load previously verified tweet IDs from file."""
        try:
            if os.path.exists(self.verified_tweets_file):
                with open(self.verified_tweets_file, 'r') as f:
                    return set(line.strip() for line in f)
            return set()
        except Exception as e:
            print(f"Error loading verified tweets: {e}")
            return set()

    def _save_verified_tweet(self, tweet_id: str) -> bool:
        """Save verified tweet ID to file. Returns True if tweet was newly added."""
        try:
            if tweet_id in self.verified_tweets:
                return False
            with open(self.verified_tweets_file, 'a') as f:
                f.write(f"{tweet_id}\n")
            self.verified_tweets.add(tweet_id)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save verified tweet: {e}")
            return False
        
    def _get_tweet_data(self, tweet_id: str) -> Optional[Dict]:
        """Get tweet data with specified fields."""
        return self.twitter_plugin.twitter_client.get_tweet(
            tweet_id,
            tweet_fields=['conversation_id', 'referenced_tweets', 'text', 'author_id'],
            expansions=['referenced_tweets.id']
        )

    def _get_original_tweet(self, tweet_id: str) -> Optional[Dict]:
        """Get the original (root) tweet of a thread."""
        max_retries = 3
        base_wait_time = 60  # seconds
        
        for attempt in range(max_retries):
            try:
                current_tweet = self._get_tweet_data(tweet_id)

                if not current_tweet or not current_tweet.data:
                    raise ValueError(f"Tweet with ID {tweet_id} not found")

                referenced_tweets = getattr(current_tweet.data, 'referenced_tweets', None)
                if not referenced_tweets:
                    return self._format_tweet_data(current_tweet.data)

                while referenced_tweets:
                    parent_ref = next(
                        (ref for ref in referenced_tweets if ref.type == 'replied_to'),
                        None
                    )
                    if not parent_ref:
                        break

                    # Add delay between API calls
                    time.sleep(2)
                    
                    current_tweet = self._get_tweet_data(str(parent_ref.id))
                    if not current_tweet or not current_tweet.data:
                        break
                    
                    referenced_tweets = getattr(current_tweet.data, 'referenced_tweets', None)

                return self._format_tweet_data(current_tweet.data)

            except Exception as e:
                if "429" in str(e):
                    wait_time = base_wait_time * (attempt + 1)  # Exponential backoff
                    print(f"[WARN] Rate limit hit, waiting {wait_time} seconds (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    if attempt == max_retries - 1:  # Last attempt
                        raise RuntimeError(f"Rate limit persisted after {max_retries} retries")
                    continue  # Try again
                raise  # Re-raise other exceptions

    def _format_tweet_data(self, tweet_data) -> Dict:
        """Format tweet data into consistent structure."""
        return {
            'id': str(tweet_data.id),
            'text': tweet_data.text,
            'author_id': tweet_data.author_id
        }

    def _extract_proof_from_tweet(self, tweet_text: str) -> Optional[Dict]:
        """Extract proof ID from tweet text."""
        try:
            print(f"Attempting to extract proof from tweet text: {tweet_text}")
            proof_match = re.search(
                r'Proof ID:\s*(\S+)\s*$',
                tweet_text,
                re.IGNORECASE
            )
            if proof_match:
                proof_id = proof_match.group(1)
                print(f"Found proof ID: {proof_id}")
                return {"proof_id": proof_id}

            print("No proof ID found in tweet text")
            return None
        except Exception as e:
            print(f"Error extracting proof ID: {e}")
            return None

    def _handle_verification_response(
        self,
        verification_result: bool,
        proof_id: str,
        is_previously_verified: bool,
        original_tweet_id: str,
        reply_tweet_id: str,
        original_author_id: str
    ) -> Tuple[FunctionResultStatus, str, Dict]:
        """Handle verification result and post appropriate responses."""
        try:
            reply_tweet_fn = self.twitter_plugin.get_function('reply_tweet')
            base_reply_text = self._generate_reply_text(
                verification_result,
                proof_id,
                is_previously_verified
            )

            # Add mention of original author if replying to a different tweet
            if reply_tweet_id != original_tweet_id:
                reply_text = f"@{original_author_id} {base_reply_text}"
            else:
                reply_text = base_reply_text

            # Only reply to the incoming tweet
            reply_tweet_fn(reply_tweet_id, reply_text)

            return (
                FunctionResultStatus.DONE,
                "Proof verification completed and response posted",
                {
                    "valid": verification_result,
                    "original_tweet_id": original_tweet_id,
                    "proof_id": proof_id
                }
            )
        except Exception as e:
            print(f"Error posting verification reply: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"Error posting reply: {str(e)}",
                {}
            )

    def _generate_reply_text(
        self,
        verification_result: bool,
        proof_id: str,
        is_previously_verified: bool
    ) -> str:
        """Generate appropriate reply text based on verification result."""
        if verification_result:
            if not is_previously_verified:
                return f"[SUCCESS] Agent verified by Seraph x Opacity\n└─ Proof {proof_id}"
            else:
                return f"[SUCCESS] Trust strengthened\n└─ Verifiable inference proof {proof_id}"
        else:
            if not is_previously_verified:
                return f"[FAILED] Invalid inference detected\n└─ Proof {proof_id}"
            else:
                return f"[FAILED] Trust diminished\n└─ Proof {proof_id}"
    
    def verify_tweet_thread(self, tweet_id: str) -> tuple:
        """Verify a proof from the original tweet in a thread."""
        try:
            if not tweet_id or not isinstance(tweet_id, str):
                return FunctionResultStatus.FAILED, "Invalid tweet ID provided", {}
            
            try:
                original_tweet = self._get_original_tweet(tweet_id)
                if not original_tweet:
                    return FunctionResultStatus.FAILED, "Could not retrieve original tweet", {}
            except Exception as e:
                return FunctionResultStatus.FAILED, f"Error retrieving tweet: {str(e)}", {}
            
            original_tweet_id = original_tweet['id']
            if original_tweet_id in self.verified_tweets:
                try:
                    author_data = self.twitter_plugin.twitter_client.get_user(id=original_tweet['author_id'])
                    author_username = author_data.data.username
                except Exception as e:
                    author_username = original_tweet['author_id']
                    
                reply_tweet_fn = self.twitter_plugin.get_function('reply_tweet')
                
                if tweet_id != original_tweet_id:
                    reply_text = f"@{author_username} [INFO] Tweet already verified\n└─ Original tweet: {original_tweet_id}"
                else:
                    reply_text = f"[INFO] Tweet already verified"
                    
                reply_tweet_fn(tweet_id, reply_text)
                
                return (
                    FunctionResultStatus.DONE,
                    "Tweet was previously verified",
                    {"original_tweet_id": original_tweet_id}
                )

            reply_tweet = self._get_tweet_data(tweet_id)
            if not reply_tweet or not reply_tweet.data:
                return FunctionResultStatus.FAILED, "Could not retrieve reply tweet", {}

            reply_text = reply_tweet.data.text

            original_tweet_author = original_tweet['author_id']
            # Check if author is already verified before proceeding
            is_previously_verified = str(original_tweet_author) in self.verified_agents
            print(f"[DEBUG] Author {original_tweet_author} verification status: {'verified' if is_previously_verified else 'not verified'}")
            print(f"[DEBUG] Current verified agents: {self.verified_agents}")

            try:
                author_data = self.twitter_plugin.twitter_client.get_user(id=original_tweet_author)
                author_username = author_data.data.username
            except Exception as e:
                print(f"Error getting author username: {e}")
                author_username = original_tweet_author

            proof_data = self._extract_proof_from_tweet(original_tweet['text'])
            if not proof_data:
                return (
                    FunctionResultStatus.FAILED,
                    "No proof ID found in the original tweet",
                    {"original_tweet_id": original_tweet['id']}
                )

            try:
                proof_id = proof_data["proof_id"]
                
                try:
                    proof_response = requests.get(
                        f"{self.opacity_plugin.prover_url}/api/logs/{proof_id}"
                    )
                    if not proof_response.ok:
                        reply_tweet_fn = self.twitter_plugin.get_function('reply_tweet')
                        reply_text = f"[FAILED] Invalid or expired proof\n└─ Proof {proof_id}"
                        
                        reply_tweet_fn(tweet_id, reply_text)
                        
                        return (
                            FunctionResultStatus.DONE,
                            "Invalid proof ID - verification failed",
                            {
                                "valid": False,
                                "original_tweet_id": original_tweet['id'],
                                "proof_id": proof_id
                            }
                        )

                    proof_data = proof_response.json()
                    verification_result = self.opacity_plugin.verify_proof({"proof": proof_data})

                except requests.RequestException as e:
                    print(f"Error fetching proof data: {e}")
                    return (
                        FunctionResultStatus.FAILED,
                        f"Error fetching proof data: {str(e)}",
                        {
                            "original_tweet_id": original_tweet['id'],
                            "proof_id": proof_id
                        }
                    )

                # Continue with existing verification logic
                if verification_result:
                    self._save_verified_tweet(original_tweet_id)
                    if not is_previously_verified:
                        self._save_verified_agent(str(original_tweet_author))
                        print(f"[DEBUG] Saved new verified agent: {original_tweet_author}")

                return self._handle_verification_response(
                    verification_result,
                    proof_id,
                    is_previously_verified,
                    original_tweet['id'],
                    tweet_id,
                    author_username
                )

            except Exception as e:
                error_msg = f"Error during proof verification: {str(e)}"
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
        """Create worker with thread verification capability."""
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
        """Run the worker on a single tweet thread."""
        self.worker.run(f"Verify tweet thread: {tweet_id}")


def main():
    worker = OpacityVerificationWorker()
    test_tweet_id = 1886017939822047367
    worker.run(test_tweet_id)
    
    # 


if __name__ == "__main__":
    main()