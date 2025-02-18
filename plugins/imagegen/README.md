# Image Generator Plugin for GAME SDK

TogetherAI has a free flux schnell image generator, which we'll use here because it's free.
Can change endpoints, params, etc to suit your needs.

## Features
- Generate images based on prompt
- Receive images as temporary URL or B64 objects

## Available Functions

1. `generate_image(prompt: str)` - Generates image based on prompt

## Setup and configuration
1. Set the following environment variables:
  - `TOGETHER_API_KEY`: Create an API key by [creating an account](https://together.ai).

2. Import and initialize the plugin to use in your worker:
```python
from plugins.imagegen.imagegen_plugin import ImageGenPlugin

imagegen_plugin = ImageGenPlugin(
  api_key=os.environ.get("TOGETHER_API_KEY"),
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

generate_image_worker = Worker(
    api_key=os.environ.get("TOGETHER_API_KEY"),
    description="Worker for generating AI images based on prompt",
    get_state_fn=get_state_fn,
    action_space=[
        imagegen_plugin.get_function("generate_image"),
    ],
)

generate_image_worker.run("Cute anime girl with twitter logo")
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
export TOGETHER_API_KEY="your-together-api-key"
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