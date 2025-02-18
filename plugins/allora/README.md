# Allora Network Plugin for GAME SDK

The [Allora Network](https://allora.network) plugin seamlessly empowers G.A.M.E agents with real-time, advanced, self-improving AI inferences, delivering high-performance insights without introducing any additional complexity.

## Features
- Get price inferences for various assets and timeframes
- Get all available topics on Allora Network
- Fetch inferences by topic ID

## Available Functions

1. `get_price_inference(asset: str, timeframe: str)` - Fetches the price inferences for the specified asset and a timeframe
2. `get_all_topics()` - Retrieves all available topics on Allora Network
3. `get_inference_by_topic_id(topic_id: int)` - Fetches the latest inference for a specific topic

## Setup and configuration
1. Set the following environment variables:
  - `ALLORA_API_KEY`: Create an API key by [creating an account](https://developer.upshot.xyz/signup).
  - `ALLORA_CHAIN_SLUG` (Optional): Must be one of: `mainnet`, `testnet`. Default value: `testnet`

2. Import and initialize the plugin to use in your worker:
```python
from plugins.allora.allora_plugin import AlloraPlugin

allora_network_plugin = AlloraPlugin(
  chain_slug=os.environ.get("ALLORA_CHAIN_SLUG", ChainSlug.TESTNET),
  api_key=os.environ.get("ALLORA_API_KEY", "UP-17f415babba7482cb4b446a1"),
)
```

**Basic worker example:**
```python
def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on the function results
    """
    init_state = {}

    if current_state is None:
        return init_state

    # Update state with the function result info
    current_state.update(function_result.info)

    return current_state

price_inference_worker = Worker(
    api_key=os.environ.get("GAME_API_KEY"),
    description="Worker specialized in using Allora Network to get price inferences",
    get_state_fn=get_state_fn,
    action_space=[
        allora_network_plugin.get_function("get_price_inference"),
    ],
)

price_inference_worker.run("Query the price of BTC in 5min")
```

## Running examples

To run the examples showcased in the plugin's directory, follow these steps:

1. Install dependencies:
```
poetry install
```

2. Set up environment variables:
```
export GAME_API_KEY="your-game-api-key"
export ALLORA_API_KEY="your-allora-api-key" # Default key: UP-17f415babba7482cb4b446a1
export ALLORA_CHAIN_SLUG="testnet"  # or "mainnet"
```

3. Run example scripts:

Example worker:
```
poetry run python ./examples/example-worker.py  
```

Example agent:
```
poetry run python ./examples/example-agent.py
```
