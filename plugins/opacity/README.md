# Opacity Plugin for Game Framework

The Opacity plugin provides integration with the Opacity protocol for verifying AI inference proofs. It includes functionality for verifying proofs and interacting with Twitter for automated verification responses.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/opengame/game-python.git
cd game-python/plugins/opacity
```

2. Install dependencies:
```bash
pip install -e .
```

## Configuration

Set up the required environment variables:

```bash
# Required for Opacity verification
OPACITY_PROVER_URL=https://prover.opacity.com

# Required for Twitter integration
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET_KEY=your_api_secret_key
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_CLIENT_KEY=your_client_key
TWITTER_CLIENT_SECRET=your_client_secret

# Required for Game Framework
GAME_API_KEY=your_game_api_key
```

## Usage

### Basic Proof Verification

```python
from opacity_game_sdk.opacity_plugin import OpacityPlugin

# Initialize the plugin
opacity_plugin = OpacityPlugin()

# Verify a proof
result = {
    "proof_id": "abc123"  # Proof ID from Opacity
}
is_valid = opacity_plugin.verify_proof(result)
print(f"Proof is valid: {is_valid}")
```

### Twitter Verification Worker

The plugin includes a worker that can verify proofs from Twitter threads:

```python
from opacity_game_sdk.examples.opacity_worker import OpacityVerificationWorker

# Initialize the worker
worker = OpacityVerificationWorker()

# Verify a tweet thread
tweet_id = "1234567890"  # ID of any tweet in the thread
worker.run(tweet_id)
```

### Twitter Verification Agent

For continuous monitoring of Twitter mentions and automated verification:

```python
from opacity_game_sdk.examples.opacity_agent import check_mentions
import threading

# Create and start the mention checker thread
mention_checker = threading.Thread(target=check_mentions, daemon=True)
mention_checker.start()
```

## Examples

### Verifying a Tweet Thread

The worker can verify proofs in Twitter threads by finding the original tweet and extracting the proof ID:

```python
worker = OpacityVerificationWorker()

# Verify a thread containing a proof
result = worker.verify_tweet_thread("1234567890")
if result[0] == FunctionResultStatus.DONE:
    print(f"Verification successful: {result[2]}")
```

### Running the Twitter Bot

The agent can run as a Twitter bot that automatically verifies proofs when mentioned:

```python
# Run the agent (from examples/opacity_agent.py)
if __name__ == "__main__":
    mention_checker = threading.Thread(target=check_mentions, daemon=True)
    mention_checker.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
```

## Tweet Format

For the verification bot to work, tweets should include the proof ID in the following format:
```
Your tweet content... Proof ID: abc123
```

The bot will:
1. Look for mentions
2. Find the original tweet in the thread
3. Extract the proof ID
4. Verify the proof
5. Reply with the verification result

## License

This project is licensed under the MIT License - see the LICENSE file for details.