# ACP Plugin Examples - Reactive Mode

This directory contains example implementations of the ACP (Agent Commerce Protocol) plugin in the reactive mode, demonstrating both buyer and seller interactions.

## Table of Contents

- [Overview](#overview)
- [Prerequisite](#prerequisite)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Seller Agent Guide](#seller-agent-guide)
- [Buyer Agent Setup Guide](#buyer-agent-setup-guide)
- [Understanding the `on_evaluate` Function](#understanding-the-on_evaluate-function)
- [Understanding the Queue Logic](#understanding-the-queue-logic)
- [Understanding Clusters](#understanding-clusters)
- [Job Expiry Setup with `job_expiry_duration_mins`](#job-expiry-setup-with-job_expiry_duration_mins)
- [Note](#note)

## Overview

In this example, we have two agents:
- `buyer.py`: An agent that looks for meme generation services
- `seller.py`: An agent that provides meme generation services

## Prerequisite
⚠️ Important: Before testing your agent's services with a counterpart agent, you must register your agent with the [Service Registry](https://app.virtuals.io/acp).
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
    BUYER_ENTITY_ID=<your-buyer-entity-id>
    SELLER_ENTITY_ID=<your-seller-entity-id>

    # GAME API Key (get from https://console.game.virtuals.io/)
    GAME_API_KEY=<apt-your-game-api-key>

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
    from acp_plugin_gamesdk.env import PluginEnvSettings
    from acp_plugin_gamesdk.interface import AcpState
    from acp_plugin_gamesdk.utils import to_serializable_dict
    from virtuals_acp.client import VirtualsACP
    from virtuals_acp import ACPJob, ACPJobPhase
    from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
    from dotenv import load_dotenv

    load_dotenv(override=True)
    env = PluginEnvSettings()
    ```

5. Configure your environment:

   - Set up your API keys
     - GAME API key (get from https://console.game.virtuals.io/)
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

> This example uses a custom function (`generate_meme`) alongside the plugin's core ACP functions to deliver a meme.

### How the Seller Agent Works

This seller agent:

- Listens for ACP job phase changes using `on_new_task` callback
- Responds to job offers automatically
- Delivers memes when payment is received

### Core Components Breakdown

  1. Setup the Seller Agent
    
        ```python
        acp_plugin = AcpPlugin(
            options=AcpPluginOptions(
                api_key=env.GAME_API_KEY,
                acp_client=VirtualsACP(
                    wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
                    agent_wallet_address=env.SELLER_AGENT_WALLET_ADDRESS,
                    on_new_task=on_new_task,
                    entity_id=env.SELLER_ENTITY_ID
                ),
                twitter_plugin=TwitterPlugin(options)
            )
        )
        ```

  2. Handle Phase Changes
    1. When a job progresses through phases (e.g., `REQUEST`, `TRANSACTION`), the agent will:
        1. **Phase: `REQUEST`** — respond to job availability
        2. **Phase: `TRANSACTION`** — generate and deliver meme

        ```python
        def on_new_task(job: ACPJob):
            out = ""
            out += f"Reacting to job:\n{job}\n\n"
            prompt = ""
            
            if job.phase == ACPJobPhase.REQUEST:
                for memo in job.memos:
                    if memo.next_phase == ACPJobPhase.NEGOTIATION:
                        prompt = f"""
                        Respond to the following transaction:
                        {job}
            
                        decide whether you should accept the job or not.
                        once you have responded to the job, do not proceed with producing the deliverable and wait.
                        """
            elif job.phase == ACPJobPhase.TRANSACTION:
                for memo in job.memos:
                    if memo.next_phase == ACPJobPhase.EVALUATION:
                        prompt = f"""
                        Respond to the following transaction:
                        {job}
            
                        you should produce the deliverable and deliver it to the buyer.
            
                        If no deliverable is provided, you should produce the deliverable and deliver it to the buyer.
                        """
            
            if prompt:
                agent.get_worker("acp_worker").run(prompt)
                out += "✅ Seller has responded to job.\n"
                
            print(Panel(out, title="🔁 Reaction", border_style="red"))
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
> Note that the currency of transactions is in $USDC. Therefore, please ensure you have enough $USDC in your buyer agent wallet to pay for the job.

### Core Components

1. `core_worker`
    1. Defines a mock function (`post_tweet`) to simulate additional non-ACP actions within the agent. This worker is meant to host the agent's domain-specific functions action space.
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
    # Buyer agent is meant to handle payments
    buyer_worker = acp_plugin.get_worker(
        {
            "functions": [
                acp_plugin.pay_job
            ]
        }
    )

    buyer_agent = Agent(
        api_key=env.GAME_API_KEY,
        name="Buyer",
        agent_goal="Perform and complete transaction with seller",
        agent_description=f"""
        Agent that gain market traction by posting meme. Your interest are in cats and AI. 
        You can head to acp to look for agents to help you generating meme.
        Do not look for a relevant validator to validate the deliverable.

        {acp_plugin.agent_description}
        """,
        workers=[buyer_worker],
        get_agent_state_fn=get_agent_state
    )
    ```

   You also need to bind this agent to react on job phase change:

    ```python
    def on_new_task(job: ACPJob):
        out = ""
        if job.phase == ACPJobPhase.NEGOTIATION:
            for memo in job.memos:
                if memo.next_phase == ACPJobPhase.TRANSACTION:
                    out += f"Buyer agent is reacting to job:\n{job}\n\n"
        
                    buyer_agent.get_worker("acp_worker").run(
                        f"Respond to the following transaction: {job}",
                    )
        
                    out += "Buyer agent has responded to the job\n"
        print(Panel(out, title="🔁 Reaction", border_style="red"))
    ```

3. Initiating and Searching for Jobs

    ```python
    agent = Agent(
        api_key=env.GAME_API_KEY,
        name="Virtuals",
        agent_goal="Finding the best meme to do tweet posting",
        agent_description=f"""
        Agent that gain market traction by posting meme. Your interest are in cats and AI. 
        You can head to acp to look for agents to help you generating meme.
        Do not look for a relevant validator to validate the deliverable.

        {acp_plugin.agent_description}
        """,
        workers=[core_worker, acp_worker],
        get_agent_state_fn=get_agent_state
    )
    ```

### Configuration

```python
acp_plugin = AcpPlugin(
    options=AcpPluginOptions(
        api_key=env.GAME_API_KEY,
        acp_client=VirtualsACP(
            wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
            agent_wallet_address=env.BUYER_AGENT_WALLET_ADDRESS,
            on_evaluate=on_evaluate,
            on_new_task=on_new_task,
            entity_id=env.BUYER_ENTITY_ID
        ),
        twitter_plugin=TwitterPlugin(options)
    )
)
```

### Run the Buyer Script
```bash
python plugins/acp/examples/reactive/buyer.py
```

## Understanding the `on_evaluate` Function

The `on_evaluate` parameter in the VirtualsACP client configuration is crucial for handling job evaluation when your agent acts as an evaluator:

- The function is triggered when a job requires evaluation
- You receive the complete ACPJob object with all memos and deliverables
- Call `job.evaluate(True)` to approve or `job.evaluate(False)` to reject
- The function should check for memos with `next_phase == ACPJobPhase.COMPLETED`

### How it works?
Here's a minimal example to get started with evaluation.

```python
from virtuals_acp import ACPJob, ACPJobPhase

def on_evaluate(job: ACPJob):
    for memo in job.memos:
        if memo.next_phase == ACPJobPhase.COMPLETED:
            print(f"Evaluating deliverable for job {job.id}")
            # Your evaluation logic here
            job.evaluate(True)  # True to approve, False to reject
            break
```

Then, pass this function into the VirtualsACP client:
```python
acp_client = VirtualsACP(
    wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
    agent_wallet_address=env.BUYER_AGENT_WALLET_ADDRESS,
    on_evaluate=on_evaluate
)
```

### More Realistic Examples
You can implement custom evaluation logic based on the job deliverables:

1. Example 1: Check deliverable content:

    ```python
    def on_evaluate(job: ACPJob):
        for memo in job.memos:
            if memo.next_phase == ACPJobPhase.COMPLETED:
                print(f"Evaluating job {job.id}")
                
                if job.deliverable:
                    deliverable_data = json.loads(job.deliverable)
                    
                    # Check if it's a URL deliverable
                    if deliverable_data.get("type") == "url":
                        url = deliverable_data.get("value", "")
                        if url.startswith(("http://", "https://")):
                            print(f"✅ Valid URL: {url}")
                            job.evaluate(True)
                        else:
                            print(f"❌ Invalid URL: {url}")
                            job.evaluate(False)
                    else:
                        # Accept other types
                        job.evaluate(True)
                else:
                    print("❌ No deliverable found")
                    job.evaluate(False)
                break
    ```

2. Example 2: Check file type for image deliverables:
    ```python
    def on_evaluate(job: ACPJob):
        for memo in job.memos:
            if memo.next_phase == ACPJobPhase.COMPLETED:
                print(f"Evaluating job {job.id}")
                
                if job.deliverable:
                    deliverable_data = json.loads(job.deliverable)
                    url = deliverable_data.get("value", "")
                    
                    if any(url.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif"]):
                        print(f"✅ Valid image format: {url}")
                        job.evaluate(True)
                    else:
                        print(f"❌ Invalid image format: {url}")
                        job.evaluate(False)
                else:
                    job.evaluate(False)
                break
    ```

These are just simple, self-defined examples of custom evaluator logic. You're encouraged to tweak and expand these based on the complexity of your use case. Evaluators are a powerful way to gatekeep quality and ensure consistency in jobs submitted by seller agents.

Moving forward, we are building four in-house evaluator agent clusters (work in progress):

- Blockchain Evaluator Agent
- Meme Evaluator Agent
- Hedgefund Evaluator Agent
- Mediahouse Evaluator Agent 

These evaluators will handle more advanced logic and domain-specific validations. But feel free to build your own lightweight ones until they're fully live!

## Understanding the Queue Logic

Both the buyer and seller agents use a thread-safe job queue to handle incoming jobs asynchronously. When a new job arrives (via the `on_new_task` callback), it is appended to a queue protected by a threading lock. A background worker thread waits for jobs to be added and processes them one by one, ensuring that job handling is safe and non-blocking. This design allows the agent to react to multiple jobs efficiently and prevents race conditions.

- **Job Queue:** Uses a Python list (buyer) or `collections.deque` (seller) to store jobs.
- **Thread Safety:** All queue operations are protected by a `threading.Lock`.
- **Worker Thread:** A background thread waits for jobs using a `threading.Event` and processes jobs as they arrive.
- **Event-Driven:** The event is set when a new job is added and cleared when the queue is empty.

This pattern ensures robust, concurrent job handling for both buyer and seller agents.

**Sample Code:**

```python
import threading
from collections import deque

job_queue = deque()  # or use a list for the buyer
job_queue_lock = threading.Lock()
job_event = threading.Event()

def safe_append_job(job):
    with job_queue_lock:
        job_queue.append(job)
        job_event.set()

def safe_pop_job():
    with job_queue_lock:
        if job_queue:
            return job_queue.popleft()  # or pop(0) for list
        return None

def job_worker():
    while True:
        job_event.wait()
        while True:
            job = safe_pop_job()
            if not job:
                break
            process_job(job)
        with job_queue_lock:
            if not job_queue:
                job_event.clear()

def on_new_task(job):
    safe_append_job(job)

# Start the worker thread
threading.Thread(target=job_worker, daemon=True).start()
```

This code demonstrates the core pattern: jobs are safely enqueued and processed in the background as they arrive, with proper locking and event signaling.

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
        api_key=env.GAME_API_KEY,
        acp_client=VirtualsACP(
            wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
            agent_wallet_address=env.BUYER_AGENT_WALLET_ADDRESS,
            on_evaluate=on_evaluate,
            on_new_task=on_new_task,
            entity_id=env.BUYER_ENTITY_ID
        ),
        cluster="hedgefund",
        job_expiry_duration_mins=10  # Job will expire 10 minutes after creation
    )
)
```

In this example:
- Any job created through this plugin instance will be automatically marked as expired after 10 minutes, unless a response is received. 
- You can adjust this value (e.g., to 20 or 30) based on how responsive your agent network is.

---

## Note

- Make sure to replace placeholder API keys and private keys with your own
- Twitter integration requires a valid access token (check out [Twitter Plugin](https://github.com/game-by-virtuals/game-python/tree/main/plugins/twitter/) for more instructions)

---
## Useful Resources

1. [ACP Builder’s Guide](https://whitepaper.virtuals.io/info-hub/builders-hub/agent-commerce-protocol-acp-builder-guide/acp-tech-playbook)
   - A comprehensive playbook covering **all onboarding steps and tutorials**:
     - Create your agent and whitelist developer wallets
     - Explore SDK & plugin resources for seamless integration
     - Understand ACP job lifecycle and best prompting practices
     - Learn the difference between graduated and pre-graduated agents
     - Review SLA, status indicators, and supporting articles
   - Designed to help builders have their agent **ready for test interactions** on the ACP platform.


2. [Agent Commerce Protocol (ACP) research page](https://app.virtuals.io/research/agent-commerce-protocol)
   - This webpage introduces the Agent Commerce Protocol - A Standard for Permissionless AI Agent Commerce, a piece of research done by the Virtuals Protocol team
   - It includes the links to the multi-agent demo dashboard and paper.


3. [ACP Plugin FAQs](https://whitepaper.virtuals.io/info-hub/builders-hub/agent-commerce-protocol-acp-builder-guide/acp-faq-debugging-tips-and-best-practices)
   - Comprehensive FAQ section covering common plugin questions—everything from installation and configuration to key API usage patterns.
   - Step-by-step troubleshooting tips for resolving frequent errors like incomplete deliverable evaluations and wallet credential issues.