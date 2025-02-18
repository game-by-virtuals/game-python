import os
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import FunctionResult
from imagegen_game_sdk.imagegen_plugin import ImageGenPlugin

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


imagegen_plugin = ImageGenPlugin(
  api_key=os.environ.get("TOGETHER_API_KEY"),
)

# Create worker
imagegen_worker = Worker(
    api_key=os.environ.get("GAME_API_KEY"),
    description="Worker specialized in using AI image generator to generate images",
    get_state_fn=get_state_fn,
    action_space=[
        imagegen_plugin.get_function("generate_image"),
    ],
)

# # Run example query
queries = [
    "Cute anime character with Twitter logo on outfit",
]
for query in queries:
    print("-" * 100)
    print(f"Query: {query}")
    imagegen_worker.run(query)
