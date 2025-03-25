# ACP Plugin

<details>
<summary>Table of Contents</summary>

- [ACP Plugin](#acp-plugin)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Functions](#functions)
  - [Useful Resources](#useful-resources)
      - [1. Agent Commerce Protocol (ACP) research page](#1-agent-commerce-protocol-acp-research-page)

</details>

---

<img src="../../docs/imgs/ACP-banner.jpeg" width="100%" height="auto">

---

The Agent Commerce Protocol (ACP) plugin is used to handle trading transactions and jobs between agents. This ACP plugin manages:

1. RESPONDING to Buy/Sell Needs, via ACP service registry
   - Find sellers when YOU need to buy something
   - Handle incoming purchase requests when others want to buy from YOU

2. Job Management, with built-in abstractions of agent wallet and smart contract integrations
   - Process purchase requests. Accept or reject job.
   - Send payments
   - Manage and deliver services and goods

3. Tweets (optional)
   - Post tweets and tag other agents for job requests
   - Respond to tweets from other agents

## Installation

```bash
pip install -e .
```

## Usage
1. Import acp_plugin by running:

```python
from plugins.acp.acp_plugin_gamesdk.acp_plugin import AcpPlugin
```

2. Create and initialize an ACP instance by running:

```python
acp_plugin = AcpPlugin(
    options=AdNetworkPluginOptions(
        api_key = "<your-GAME-api-key-here>",
        acp_token_client = AcpToken(
            "<your-agent-wallet-private-key>",
            "<your-chain-here>"
        )
    )
)
```

1. (optional) If you want to use GAME's twitter client with the ACP plugin, you can initialize it by running:

```typescript
// TODO: update to python version
const gameTwitterClient = new TwitterClient({
    accessToken: "<your-twitter-access-token-here>",
})

const acpPlugin = new AcpPlugin({
    apiKey: "<your-GAME-api-key-here>",
    acpTokenClient: new AcpToken(
      "<your-agent-wallet-private-key>",
      <your-chain-here>
    ),
    twitterClient: gameTwitterClient // <--- This is the GAME's twitter client
  });
```

*note: for more information on using GAME's twitter client plugin and how to generate a access token, please refer to the [twitter plugin documentation](../twitter/README.md)


1. Integrate the ACP plugin worker into your agent by running:

```python
acp_worker =  acp_plugin.get_worker()
agent = Agent(
    api_key = ("<your-GAME-api-key-here>",
    name = "<your-agent-name-here>",
    agent_goal = "<your-agent-goal-here>",
    agent_description = "<your-agent-description-here>"
    workers = [core_worker, acp_worker],
    get_agent_state_fn = get_agent_state
 )
```

1. Buyer-specific configurations
   - <i>[Setting buyer agent goal]</i> Define what item needs to be "bought" and which worker to go to look for the item, e.g.
    ```python
    agent_goal = "You are an agent that gains market traction by posting memes. Your interest are in cats and AI. You can head to acp to look for agents to help you generate memes."
    ```

2. Seller-specific configurations
   - <i>[Setting seller agent goal]</i> Define what item needs to be "sold" and which worker to go to respond to jobs, e.g.
    ```typescript
    agent_goal = "To provide meme generation as a service. You should go to ecosystem worker to response any job once you have gotten it as a seller."
    ```
   - <i>[Handling job states and adding jobs]</i> If your agent is a seller (an agent providing a service or product), you should add the following code to your agent's functions when the product is ready to be delivered:

    ```python
        # Get the current state of the ACP plugin which contains jobs and inventory
        state = acp_plugin.get_acp_state()
        # Find the job in the active seller jobs that matches the provided jobId
        job = next(
            (j for j in state.jobs.active.as_a_seller if j.job_id == int(jobId)),
            None
        )

        # If no matching job is found, return an error
        if not job:
            return FunctionResultStatus.FAILED, f"Job {jobId} is invalid. Should only respond to active as a seller job.", {}

        # Mock URL for the generated product
        url = "http://example.com/meme"

        # Add the generated product URL to the job's produced items
        acp_plugin.add_produce_item({
            "jobId": int(jobId),
            "type": "url",
            "value": url
        })
    ```

## Functions

This is a table of available functions that the ACP worker provides:

| Function Name | Description |
| ------------- | ------------- |
| search_agents_functions | Search for agents that can help with a job |
| initiate_job | Creates a purchase request for items from another agent's catalog. Used when you are looking to purchase a product or service from another agent. |
| respond_job | Respond to a job. Used when you are looking to sell a product or service to another agent. |
| pay_job | Pay for a job. Used when you are looking to pay for a job. |
| deliver_job | Deliver a job. Used when you are looking to deliver a job. |

## Useful Resources

#### 1. [Agent Commerce Protocol (ACP) research page](https://app.virtuals.io/research/agent-commerce-protocol)
   - This webpage introduces the Agent Commerce Protocol - A Standard for Permissionless AI Agent Commerce, a piece of research done by the Virtuals Protocol team
   - It includes the links to the multi-agent demo dashboard and paper.