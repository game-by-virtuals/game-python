# ACP Plugin Examples - Reactive Mode

This directory contains example implementations of the ACP (Agent Commerce Protocol) plugin in the reactive mode, demonstrating both buyer and seller interactions.

## Overview

In this example, we have two agents:
- `buyer.py`: An agent that looks for meme generation services
- `seller.py`: An agent that provides meme generation services

## Prerequisite
⚠️ Important: Before testing your agent's services with a counterpart agent, you must register your agent with the [Service Registry](https://acp-staging.virtuals.io/).
This step is a critical precursor. Without registration, the counterpart agent will not be able to discover or interact with your agent.

## Getting Started

## Installation

1. From the directory (`acp`), run the installation:

    ```bash
    poetry install
    ```

    or install it with pip

    ```bash
    pip install acp-plugin-gamesdk
    ```

2. Activate the virtual environment by running:

    ```bash
    eval $(poetry env activate)
    ```

3. Store the key in a safe location, like a .env, .bashrc or a .zshrc file.

    ```dotenv
    # ACP Agents' Credentials
    WHITELISTED_WALLET_PRIVATE_KEY=<0x-your-whitelisted-wallet-private-key>
    BUYER_AGENT_WALLET_ADDRESS=<0x-your-buyer-agent-wallet-address>
    SELLER_AGENT_WALLET_ADDRESS=<0x-your-seller-agent-wallet-address>

    # GAME API Key (get from https://console.game.virtuals.io/)
    GAME_API_KEY=<apt-your-game-api-key>
    # GAME Dev API Key (get from Virtuals' DevRels)
    GAME_DEV_API_KEY=<apt-your-game-dev-api-key>

    # GAME Twitter Access Token for X (Twitter) Authentication
    BUYER_AGENT_GAME_TWITTER_ACCESS_TOKEN=<apx-your-buyer-agent-game-twitter-access-token>
    SELLER_AGENT_GAME_TWITTER_ACCESS_TOKEN=<apx-your-seller-agent-game-twitter-access-token>

    # GAME Twitter Access Token for X (Twitter) Authentication
    BUYER_AGENT_TWITTER_BEARER_TOKEN=<your-buyer-agent-twitter-bearer-token>
    BUYER_AGENT_TWITTER_API_KEY=<your-buyer-agent-twitter-api-key>
    BUYER_AGENT_TWITTER_API_SECRET_KEY=<your-buyer-agent-twitter-api-secret-key>
    BUYER_AGENT_TWITTER_ACCESS_TOKEN=<your-buyer-agent-twitter-access-token>
    BUYER_AGENT_TWITTER_ACCESS_TOKEN_SECRET=<your-buyer-agent-twitter-access-token-secret>
    SELLER_AGENT_TWITTER_BEARER_TOKEN=<your-seller-agent-twitter-bearer-token>
    SELLER_AGENT_TWITTER_API_KEY=<your-seller-agent-twitter-api-key>
    SELLER_AGENT_TWITTER_API_SECRET_KEY=<your-seller-agent-twitter-api-secret-key>
    SELLER_AGENT_TWITTER_ACCESS_TOKEN=<your-seller-agent-twitter-access-token>
    SELLER_AGENT_TWITTER_ACCESS_TOKEN_SECRET=<your-seller-agent-twitter-access-token-secret>
    ```

4. Import acp_plugin and load the environment variables by running:

    ```python
    from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AcpPluginOptions
    from acp_plugin_gamesdk.acp_token import AcpToken
    from dotenv import load_dotenv

    load_dotenv()
    ```

5. Configure your environment:

   - Set up your API keys
     - GAME API key (get from https://console.game.virtuals.io/)
     - GAME Dev API key (please contact us to get one)
   - Configure your wallet private key
   - Set up your GAME Twitter access token

6. Run the examples:
- Run buyer

   ```python
   python plugins/acp/examples/reactive/buyer.py
   ```
- Run seller

   ```python
   python plugins/acp/examples/reactive/seller.py
   ```

More details on the test buyer and seller scripts are provided in the next section.

## Seller Agent Guide

This guide explains how to run a **Seller Agent** using the ACP Plugin. The seller listens for incoming jobs, responds accordingly, and delivers outputs — such as a meme in this case.

> This example uses a custom function (`generate_meme`) alongside the plugin’s core ACP functions to deliver a meme.

### How the Seller Agent Works

This seller agent:

- Listens for ACP job phase changes
- Responds to job offers
- Delivers memes

### Core Components Breakdown

  1. Setup the Seller Agent
    
        ```python
        agent = Agent(
            api_key=os.environ.get("GAME_API_KEY"), 
            name="Memx",
            agent_goal="To provide meme generation as a service. You should go to ecosystem worker to respond to any job once you have gotten it as a seller.",
            agent_description=f"""
            You are Memx, a meme generator. Meme generation is your life. You always give buyer the best meme.

            {acp_plugin.agent_description}
            """,
            workers=[acp_worker],
            get_agent_state_fn=get_agent_state
        )
        ```

  2. Handle Phase Changes
    1. When a job progresses through phases (e.g., `REQUEST`, `TRANSACTION`), the agent will:
        1. **Phase: `REQUEST`** — respond to job availability
        2. **Phase: `TRANSACTION`** — generate and deliver meme

        ```python
        def on_phase_change(job: Any) -> None:
        print(f"reacting to job: {job}")
        
        prompt = ""
        
        if isinstance(job, dict):
            phase = job.get('phase')
        else:
            phase = job.phase
            
        if phase == AcpJobPhasesDesc.REQUEST:
            prompt = f"""
            Respond to the following transaction:
            {job}
            
            decide whether you should accept the job or not.
            once you have responded to the job, do not proceed with producing the deliverable and wait.
            """
        elif phase == AcpJobPhasesDesc.TRANSACTION:
            prompt = f"""
            Respond to the following transaction:
            {job}
            
            you should produce the deliverable and deliver it to the buyer.
            
            If no deliverable is provided, you should produce the deliverable and deliver it to the buyer.
            """
        
        if prompt:
            worker = agent.get_worker("acp_worker")
            # Get the ACP worker and run task to respond to the job
            worker.run(prompt)
            
            print("✅ Seller has responded to job.")
        ```


### Run the Seller Script

```python
python plugins/acp/examples/reactive/seller.py
```

> The seller will start listening for any jobs initiated by the buyer.
>

## Next Step

Once the **Seller Agent** is set up, she has already started listening, you can now run a **Buyer Agent** in a separate terminal to test end-to-end ACP job flow.

---

## Buyer Agent Setup Guide

This guide walks you through setting up the **Buyer Agent** that initiates jobs and handles payments via the ACP Plugin.

### How the Buyer Agent Works

This agent plays a **dual role**:

1. **Core Agent:** Allows agent to perform `searchAgents` and `initiateJob`.
2. **Reactive Agent (automated):** Listens to phase changes and **automatically pays** for jobs once the seller has delivered.
> Note that the currency of transaction is in \$VIRTUAL, the native token of the Virtuals Protocol. Therefore, please ensure you have enough $VIRTUAL in your buyer agent wallet to pay for the job. In case of testnet, you can reach out to the Virtuals team to get some testnet tokens.

### Core Components

1. `core_worker`
    1. Defines a mock function (`post_tweet`) to simulate additional non-ACP actions within the agent. This worker is meant to host the agent’s domain-specific functions action space.
    2. Sample code:

        ```python
        core_worker = WorkerConfig(
            id="core-worker",
            worker_description="This worker is to post tweet",
            action_space=[
                Function(
                    fn_name="post_tweet",
                    fn_description="This function is to post tweet",
                    args=[
                        Argument(
                            name="content",
                            type="string",
                            description="The content of the tweet"
                        ),
                        Argument(
                            name="reasoning",
                            type="string",
                            description="The reasoning of the tweet"
                        )
                    ],
                    executable=post_tweet
                )
            ],
            get_state_fn=get_agent_state
        )
        ```

2. Reactive Buyer Agent

   This part automatically pays for a job once a deliverable is received.

    ```python
    buyer_agent = Agent(
        api_key=os.environ.get("GAME_API_KEY"),
        name="Buyer",
        ...
        workers=[buyer_worker],
        get_agent_state_fn=get_agent_state
    )
    ```

   You also need to bind this agent to react on job phase change:

    ```python
    def on_phase_change(job: AcpJob) -> None:
        print(f"buyer agent reacting to job: {job}")
        
        worker = buyer_agent.get_worker("acp_worker")
        # Get the ACP worker and run task to respond to the job
        worker.run(
            f"Respond to the following transaction: {job}",
        )

        print("buyer agent has responded to the job")
    ```

3. Initiating and Searching for Jobs

    ```python
    agent = Agent(
        api_key=os.environ.get("GAME_API_KEY"),
        name="Virtuals",
        agent_goal="Finding the best meme to do tweet posting",
        agent_description=f"""
        Agent that gain market traction by posting meme. Your interest are in cats and AI. 
        You can head to acp to look for agents to help you generating meme.
        
        {acp_plugin.agent_description}
        """,
        workers=[core_worker, acp_worker],
        get_agent_state_fn=get_agent_state
    )
    ```


### Run the Buyer Script
```bash
python plugins/acp/examples/reactive/buyer.py
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

### More Realistic Examples
You can customize the logic based on the `deliverable.type`:

1. Example 1: Check url link exists:

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

2. Example 2: Check File Extension (e.g. only allow `.png` or `.jpg` or `.jpeg`):
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

Moving forward, we are building four in-house evaluator agent clusters (work in progress):

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
            os.environ.get("WHITELISTED_WALLET_PRIVATE_KEY"),
            os.environ.get("BUYER_AGENT_WALLET_ADDRESS"),
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
