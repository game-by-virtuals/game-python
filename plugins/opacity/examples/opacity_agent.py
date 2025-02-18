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
from datetime import datetime, timezone, timedelta
import re
import requests
from opacity_game_sdk.opacity_plugin import OpacityPlugin
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
from opacity_worker import OpacityVerificationWorker

CHECK_INTERVAL_MINUTES = 1

# Load environment variables
load_dotenv()

# Initialize worker
opacity_worker = OpacityVerificationWorker()

def verify_mentioned_results(**kwargs) -> tuple:
    """Function to process Twitter mentions and verify proofs."""
    try:
        # Calculate the cutoff time (5 minutes ago) with RFC3339 formatting
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=CHECK_INTERVAL_MINUTES)
        formatted_time = cutoff_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"[INFO] Processing mentions after: {formatted_time}")
        
        try:
            # Get bot ID
            me = opacity_worker.twitter_plugin.twitter_client.get_me()
            if not me or not me.data:
                print("[ERROR] Could not retrieve bot's user ID")
                return FunctionResultStatus.FAILED, "Failed to get bot's user ID", {}
            bot_id = me.data.id
            
            # Add delay between API calls
            time.sleep(2)

            # Get mentions
            mentions = opacity_worker.twitter_plugin.twitter_client.get_users_mentions(
                id=bot_id,
                max_results=5,
                tweet_fields=['id', 'created_at', 'text'],
                start_time=formatted_time 
            )
        except Exception as e:
            if "429" in str(e):
                print("[WARN] Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                return FunctionResultStatus.FAILED, "Rate limit hit, please retry", {}
            raise e
        
        print("got mentions")
        print(f"Mentions type: {type(mentions)}")
        print(f"Mentions data: {mentions}")
        
        if not mentions:
            return FunctionResultStatus.DONE, "No mentions retrieved", {}
        
        # Access data through the Response object properly
        mentions_data = mentions.data if hasattr(mentions, 'data') else None
        
        if not mentions_data:
            return FunctionResultStatus.DONE, "No mentions data available", {}
        
        processed_count = 0
        verified_count = 0
        skipped_count = 0

        for mention in mentions_data:
            if not hasattr(mention, 'id'):
                print(f"Invalid mention data: {mention}")
                continue
            
            tweet_time = datetime.fromisoformat(str(mention.created_at).replace('Z', '+00:00'))

            # Skip tweets older than cutoff
            if tweet_time < cutoff_time:
                print(f"[INFO] Skipping tweet {mention.id} from {tweet_time.isoformat()} - too old")
                skipped_count += 1
                continue
            
            print("mention.id:")
            print(mention.id)
            tweet_id = int(mention.id)
            print(f"\n[INFO] Processing mention tweet ID: {tweet_id} from {tweet_time.isoformat()}")
            
            time.sleep(5)

            # Use the opacity worker to verify the tweet
            try:
                status, message, result = opacity_worker.verify_tweet_thread(str(tweet_id)) 
                if status == FunctionResultStatus.DONE and result.get("valid", False):
                    verified_count += 1
                print(f"[INFO] Verification result: {message}")
            except Exception as e:
                if "429" in str(e):
                    print("[WARN] Rate limit hit during verification, waiting 60 seconds...")
                    time.sleep(60)
                    try:
                        # One retry after rate limit wait
                        status, message, result = opacity_worker.verify_tweet_thread(str(tweet_id))
                        if status == FunctionResultStatus.DONE and result.get("valid", False):
                            verified_count += 1
                        print(f"[INFO] Retry verification result: {message}")
                    except Exception as retry_e:
                        print(f"[ERROR] Failed to verify tweet {tweet_id} on retry: {retry_e}")
                        if "429" in str(retry_e):
                            return FunctionResultStatus.FAILED, "Rate limit persists after retry", {}
                else:
                    print(f"[ERROR] Failed to verify tweet {tweet_id}: {e}")
            
            processed_count += 1
        
        result_message = (
            f"Processed {processed_count} mentions, "
            f"verified {verified_count} proofs, "
            f"skipped {skipped_count} old tweets"
        )
        print(f"\n[SUMMARY] {result_message}")
        return FunctionResultStatus.DONE, result_message, {}

    except Exception as e:
        error_msg = f"Error encountered while processing mentions: {str(e)}"
        print(f"[ERROR] {error_msg}")
        if "429" in str(e):
            time.sleep(60)
        return FunctionResultStatus.FAILED, error_msg, {}

# Action space with verification capability
action_space = [
    Function(
        fn_name="verify_mentioned_results",
        fn_description="Check Twitter mentions for Proof IDs to verify",
        args=[],
        executable=verify_mentioned_results
    )
]

# Create worker
worker = Worker(
    api_key=opacity_worker.game_api_key,
    description="Processing Twitter mentions for Opacity verification requests.",
    instruction="Monitor Twitter mentions and verify AI inference results using Opacity proofs",
    get_state_fn=opacity_worker._get_state,
    action_space=action_space
)

def check_mentions():
    """Periodically check for new mentions to process."""
    while True:
        try:
            print("\n[INFO] Starting new mention check cycle...")
            worker.run("Check Twitter mentions for verification requests")
            print("[INFO] Waiting for next check cycle...")
            time.sleep(CHECK_INTERVAL_MINUTES * 60)  # Wait between checks
        except Exception as e:
            print(f"[ERROR] Error in check_mentions loop: {e}")
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