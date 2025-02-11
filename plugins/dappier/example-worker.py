# example-worker.py
import os
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import FunctionResult
from dappier_plugin import DappierPlugin

def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on the function results
    """
    init_state = {}

    if current_state is None:
        return init_state

    if function_result.info is not None:
        current_state.update(function_result.info)

    return current_state

# Initialize the Dappier plugin
dappier_plugin = DappierPlugin(
    api_key=os.environ.get("DAPPIER_API_KEY"),
)

# Create worker for real-time search
real_time_search_worker = Worker(
    api_key=os.environ.get("GAME_API_KEY","apt-2398df69ac1c8b7ac66cdcf22043908b"),
    description="Worker specialized in performing real-time data searches using Dappier",
    get_state_fn=get_state_fn,
    action_space=[
        dappier_plugin.get_function("search_real_time_data"),
    ],
)

# Example usage
if __name__ == "__main__":
    # Using the correct AI model ID from Dappier marketplace
    AI_MODEL_ID = "am_01j06ytn18ejftedz6dyhz2b15"
    
    queries = [
        f"Search for weather in New York using ai_model_id={AI_MODEL_ID}",
        f"Get stock price of Apple using ai_model_id={AI_MODEL_ID}",
        f"Find cryptocurrency market trends using ai_model_id={AI_MODEL_ID}"
    ]
    
    for query in queries:
        print("-" * 100)
        print(f"Query: {query}")
        real_time_search_worker.run(query)