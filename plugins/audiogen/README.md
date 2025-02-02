# Audio Generator Plugin for GAME SDK

Using TogetherAI serverless inference for generating audio from text.
Can change endpoints, params, etc to suit your needs.

## Features
- Generate audio based on prompt
- Receive audio as temporary URL or B64 objects

## Available Functions

1. `generate_audio(prompt: str, voice: str)` - Generates audio based on prompt and voice to use

## Setup and configuration
1. Set the following environment variables:
  - `TOGETHER_API_KEY`: Create an API key by [creating an account](https://together.ai).

2. Import and initialize the plugin to use in your worker:
```python
from plugins.audiogen.audiogen_plugin import AudioGenPlugin

audiogen_plugin = AudioGenPlugin(
  api_key=os.environ.get("TOGETHER_API_KEY", "UP-17f415babba7482cb4b446a1"),
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

generate_audio_worker = Worker(
    api_key=os.environ.get("TOGETHER_API_KEY"),
    description="Worker for generating AI audio based on prompt",
    get_state_fn=get_state_fn,
    action_space=[
        audiogen_plugin.get_function("generate_audio"),
    ],
)

generate_audio_worker.run("Hello, I love Virtuals because they're cool")
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
export TOGETHER_API_KEY="your-together-api-key" # Default key: UP-17f415babba7482cb4b446a1
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