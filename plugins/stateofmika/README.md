# State of Mika Plugin for GAME SDK

The State of Mika Plugin plugin seamlessly empowers G.A.M.E agents with real-time, advanced, self-improving AI inferences, delivering high-performance insights without introducing any additional complexity.

## Features

- image_recognition - Analyze and describe images using AI vision
- scraper - Scrape and process content from external websites
- news - Fetch and analyze cryptocurrency and blockchain news
- token_information - Get token price and market information from DEX aggregators
- math - Perform complex mathematical calculations

## Setup and Configuration

Import and initialize the plugin to use in your worker:

```python
from game_sdk.plugins.stateofmika.functions.router import SOMRouterFunction

state_of_mika_plugin = SOMRouterFunction()
```

**Basic worker example:**

```python
def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on router responses
    """
    init_state = {
        "previous_queries": [],
        "previous_routes": []
    }

    if current_state is None:
        return init_state

    # Update state with results
    if function_result and function_result.info:
        current_state["previous_queries"].append(function_result.info.get("query", ""))
        current_state["previous_routes"].append(function_result.info.get("route", {}))

    return current_state

worker = Worker(
    api_key=game_api_key,
    description="An intelligent assistant that uses StateOfMika for routing queries",
    get_state_fn=get_state_fn,
    action_space=[router_fn]
)

worker.run("What's the latest price of Bitcoin?")
```
