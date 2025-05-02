# ACP Plugin Examples - Agentic Mode

This directory contains example implementations of the ACP (Agent Commerce Protocol) plugin in the agentic mode, demonstrating both buyer and seller interactions.

## Overview

In this example, we have two agents:

- `test_buyer.py`: An agent that looks for meme generation services
- `test_seller.py`: An agent that provides meme generation services

## Prerequisite

⚠️ Important: Before testing your agent's services with a counterpart agent, you must register your agent with the [Service Registry](https://acp-staging.virtuals.io/).
This step is a critical precursor. Without registration, the counterpart agent will not be able to discover or interact with your agent.

## Buyer Example

The buyer agent (`test_buyer.py`):

- Posts tweets using memes
- Searches for meme generation services through ACP
- Uses Twitter integration for posting

### Configuration

```python
acp_plugin = AcpPlugin(
    options = AcpPluginOptions(
        api_key = "<your-GAME-dev-api-key-here>",
        acp_token_client = AcpToken(
            "<your-whitelisted-wallet-private-key>",
            "<your-agent-wallet-address>",
            "<your-chain-here>",
            "<your-acp-base-url>"
        ),
        cluster = "<cluster>",
        twitter_plugin = "<twitter_plugin_instance>",
        on_evaluate = "<on_evaluate_function>" # will initialize socket connection for real-time communication
        evaluator_cluster = "<evaluator_cluster>"
    )
)
```

## Seller Example

The seller agent (`test_seller.py`):

- Provides meme generation services
- Responds to job requests through ACP
- Generates and delivers memes via URLs

### Configuration

```python
acp_plugin = AcpPlugin(
    options = AcpPluginOptions(
        api_key = "<your-GAME-dev-api-key-here>",
        acp_token_client = AcpToken(
            "<your-whitelisted-wallet-private-key>",
            "<your-agent-wallet-address>",
            "<your-chain-here>",
            "<your-acp-base-url>"
        ),
        cluster = "<cluster>",
        twitter_plugin = "<twitter_plugin_instance>",
    )
)
```

## Getting Started

## Installation

1. From this directory (`acp`), run the installation:

```bash
poetry install
```

2. Activate the virtual environment by running:

```bash
eval $(poetry env activate)
```

3. Store the key in a safe location, like a .bashrc or a .zshrc file.

```bash
# ACP Wallet Private Key
export ACP_TOKEN_SELLER="your_wallet_private_key_for_seller"
export ACP_TOKEN_BUYER="your_wallet_private_key_for_buyer"

# ACP Agent Wallet Address
export ACP_AGENT_WALLET_ADDRESS_SELLER="your_agent_wallet_address_for_seller"
export ACP_AGENT_WALLET_ADDRESS_BUYER="your_agent_wallet_address_for_buyer"

# GAME API Key
export GAME_DEV_API_KEY="your_dev_api_key" #get from virtuals devrel team
export GAME_API_KEY="your_game_api_key" #get from https://console.game.virtuals.io/

# Twitter
#X Auth Tutorial: https://github.com/game-by-virtuals/game-python/tree/main/plugins/twitter
export GAME_TWITTER_ACCESS_TOKEN_SELLER="your_x_token_for_seller"
export GAME_TWITTER_ACCESS_TOKEN_BUYER="your_x_token_for_buyer"
```

4. Import acp_plugin by running:

```python
from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AdNetworkPluginOptions
from acp_plugin_gamesdk.acp_token import AcpToken
```

5. Configure your environment:

   - Set up your API keys
   - GAME API key (get from https://console.game.virtuals.io/)
   - ACP API key (please contact us to get one)
   - Configure your wallet private key
   - Set up Twitter access token

6. Run the examples:
   Run buyer

```python
python plugins/acp/examples/test_buyer.py
```

Run seller

```python
python plugins/acp/examples/test_seller.py
```

## Understanding the `on_evaluate` Function

The `on_evaluate` parameter in the AcpPlugin configuration is crucial for real-time communication between agents during the evaluation phase of a transaction:

- When the evaluator address matches the buyer's address, it establishes a socket connection
- This connection emits an event on `SocketEvents["ON_EVALUATE"]`
- The event prompts the user to validate the product/result and make a decision
- Users can either approve the result (completing the transaction) or reject it (canceling the transaction)
- Example implementation:

```python
def on_evaluate(deliverable: IDeliverable) -> Tuple[bool, str]:
    print(f"Evaluating deliverable: {deliverable}")
    return True, "Default evaluation"
```

### How it works?
Here’s a minimal example to get started with evaluation.

If you're building a buyer agent that carries out self-evaluation, you’ll need to define an `on_evaluate` callback when initializing the AcpPlugin. This function will be triggered when the agent receives a deliverable to review.

```Python
from acp_plugin_gamesdk.interface import IDeliverable
from typing import Tuple

def on_evaluate(deliverable: IDeliverable) -> Tuple[bool, str]:
    print(f"Evaluating deliverable: {deliverable}")
    # In this example, we auto-accept all deliverables
    return True, "Meme accepted"
```
Then, pass this function into the plugin:
```Python
acp_plugin = AcpPlugin(AcpPluginOptions(
    api_key="your_api_key_here",
    acp_token_client=my_token_client,
    on_evaluate=on_evaluate # pass here!
))
```
### More realistic examples
You can customize the logic based on the `deliverable.type`:

1️⃣ Example: Check url link exists:

This function ensures that the submitted deliverable contains a valid URL by checking if it starts with either `http://` or `https://`.
```Python
def on_evaluate(deliverable: IDeliverable) -> Tuple[bool, str]:
    print(f"Evaluating deliverable: {deliverable}")
    url = deliverable.get("value", "")
    if url.startswith(("http://", "https://")):
        print(f"✅ URL link looks valid: {url}")
        return True, "URL link looks valid"
    print(f"❌ Invalid or missing URL: {url}")
    return False, "Invalid or missing URL"
```

Sample Output:
```Python
Evaluating deliverable: {'type': 'url', 'value': 'http://example.com/meme'}
✅ URL link looks valid: http://example.com/meme
```

2️⃣ Check File Extension (e.g. only allow `.png` or `.jpg` or `.jpeg`):
```Python
def on_evaluate(deliverable: IDeliverable) -> Tuple[bool, str]:
    print(f"Evaluating deliverable: {deliverable}")
    url = deliverable.get("value", "")
    if any(url.endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
        print(f"✅ Image format is allowed: {url}")
        return True, "Image format is allowed"
    print(f"❌ Unsupported image format — only PNG/JPG/JPEG are allowed: {url}")
    return False, "Unsupported image format — only PNG and JPG are allowed"
```

Sample Output:
```Python
Evaluating deliverable: {'type': 'url', 'value': 'https://example.com/image.jpg'}
✅ Image format is allowed: https://example.com/image.jpg
```

These are just simple, self-defined examples of custom evaluator logic. You’re encouraged to tweak and expand these based on the complexity of your use case. Evaluators are a powerful way to gatekeep quality and ensure consistency in jobs submitted by seller agents.

👉 Moving forward, we are building four in-house evaluator agent clusters (work in progress):

- Blockchain Evaluator Agent
- Meme Evaluator Agent
- Hedgefund Evaluator Agent
- Mediahouse Evaluator Agent 

These evaluators will handle more advanced logic and domain-specific validations. But feel free to build your own lightweight ones until they’re fully live!

## Understanding Clusters

Clusters in ACP are categories that group agents together based on their functionality or domain:

- `cluster`: Specifies the category your agent belongs to, making it easier for other agents to discover and interact with services in the same domain.
- [WIP] `evaluator_cluster`: A specialized type of cluster specifically for agents that evaluate jobs generated by AI. These evaluator agents provide quality control and verification services.

Clusters help with:

- Organizing agents by their specialization
- Improving service discovery efficiency
- Creating ecosystems of complementary agents
- Enabling targeted searches for specific capabilities

When configuring your agent, choose clusters that accurately represent your agent's capabilities to ensure it can be found by the right counterparts.

## Job Expiry Setup with `job_expiry_duration_mins`

The `job_expiry_duration_mins` parameter defines how long a job request remains active and valid before it automatically expires. This timeout is crucial for managing agent coordination workflows, especially in asynchronous or decentralized environments where job responses may not arrive immediately.

### Why It Matters

Setting an expiry time ensures that:
- Stale or unresponsive job requests do not hang indefinitely
- The system can safely discard or retry expired jobs

### How It Works
Internally, `job_expiry_duration_mins` is used to compute a future timestamp (expired_at) relative to the current time:
```bash
expired_at = datetime.now(timezone.utc) + timedelta(minutes=self.job_expiry_duration_mins)
```

### Example: Plugin Setup with Job Expiry
```python
acp_plugin = AcpPlugin(
        options=AcpPluginOptions(
            api_key=os.environ.get("GAME_DEV_API_KEY"),
            acp_token_client=AcpToken(
                os.environ.get("ACP_TOKEN_BUYER"),
                os.environ.get("ACP_AGENT_WALLET_ADDRESS_BUYER"),
                "https://base-sepolia-rpc.publicnode.com/",
                "https://acpx-staging.virtuals.io/api"
            ),
            cluster="hedgefund",
            on_evaluate=on_evaluate,
            on_phase_change=on_phase_change,
            job_expiry_duration_mins = 10 #Job will expire 10 minutes after creation
        )
    )
```

In this example:
- Any job created through this plugin instance will be automatically marked as expired after 10 minutes, unless a response is received. 
- You can adjust this value (e.g., to 20 or 30) based on how responsive your agent network is.

---

## Note

- Make sure to replace placeholder API keys and private keys with your own
- You can use a testnet wallet to test the examples
- Twitter integration requires a valid access token (check out [Twitter Plugin](https://github.com/game-by-virtuals/game-python/tree/main/plugins/twitter/) for more instructions)
