import os
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import FunctionResult
from audiogen_game_sdk.audiogen_plugin import AudioGenPlugin

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


audiogen_plugin = AudioGenPlugin(
  api_key=os.environ.get("TOGETHER_API_KEY", "UP-17f415babba7482cb4b446a1"),
)

# Create worker
audiogen_worker = Worker(
    api_key=os.environ.get("GAME_API_KEY"),
    description="Worker specialized in creating text to speech",
    get_state_fn=get_state_fn,
    action_space=[
        audiogen_plugin.get_function("generate_audio"),
    ],
)

# Run example query
queries = [
    "In chinese woman's voice, create speech of: Hello, I love Virtuals because they're cool",
]
for query in queries:
    print("-" * 100)
    print(f"Query: {query}")
    audiogen_worker.run(query)