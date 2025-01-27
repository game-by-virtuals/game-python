# Getting Started with GAME SDK

This guide will help you get started with the GAME SDK and create your first agent.

## Installation

1. Install via pip:
```bash
pip install game_sdk
```

2. Or install from source:
```bash
git clone https://github.com/game-by-virtuals/game-python.git
cd game-python
pip install -e .
```

## API Key Setup

1. Get your API key from the [Game Console](https://console.game.virtuals.io/)

2. Set your API key:
```bash
export VIRTUALS_API_KEY="your_api_key"
```

## Quick Start

Here's a simple example to create a weather reporting agent:

```python
from game_sdk.game.agent import Agent
from game_sdk.game.worker import Worker
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import Function, Argument

# 1. Create a function
def get_weather(city: str):
    """Get weather for a city."""
    return {
        'status': 'success',
        'data': {
            'temperature': '20°C',
            'condition': 'Sunny'
        }
    }

# 2. Create function definition
weather_fn = Function(
    fn_name="get_weather",
    fn_description="Get weather for a city",
    executable=get_weather,
    args=[
        Argument(
            name="city",
            type="string",
            description="City name"
        )
    ]
)

# 3. Create worker config
worker_config = WorkerConfig(
    id="weather_worker",
    worker_description="Provides weather information",
    get_state_fn=lambda x, y: {'requests': 0},
    action_space=[weather_fn],
    instruction="Fetch weather data"
)

# 4. Create agent
agent = Agent(
    goal="Provide weather updates",
    description="Weather reporting system"
)

# 5. Add worker and run
agent.add_worker(worker_config)
agent.compile()
agent.run()
```

## Core Concepts

### 1. Agent

The high-level planner that:
- Takes a goal and description
- Manages workers
- Makes decisions

### 2. Worker

The low-level planner that:
- Takes a description
- Executes functions
- Manages state

### 3. Function

The action executor that:
- Takes parameters
- Performs actions
- Returns results

## Next Steps

1. **Explore Examples**
   - Check the [examples](examples/) directory
   - Try modifying example code
   - Create your own examples

2. **Read Documentation**
   - [SDK Overview](sdk_overview.md)
   - [API Documentation](api/)
   - [GAME Framework](https://whitepaper.virtuals.io/developer-documents/game-framework)

3. **Join Community**
   - Join our [Discord](https://discord.gg/virtuals)
   - Follow us on [Twitter](https://twitter.com/VirtualsHQ)
   - Read our [Blog](https://blog.virtuals.io)

## Common Issues

### API Key Not Found
```python
os.environ.get('VIRTUALS_API_KEY') is None
```
Solution: Set your API key in your environment

### Worker Not Found
```python
KeyError: 'worker_id'
```
Solution: Ensure worker is added to agent before running

### Function Error
```python
ValueError: Function not found
```
Solution: Check function name matches worker's action space

## Best Practices

1. **Clear Organization**
   - Separate concerns
   - Use meaningful names
   - Document code

2. **Error Handling**
   - Handle errors gracefully
   - Log errors
   - Provide feedback

3. **Testing**
   - Write unit tests
   - Test edge cases
   - Verify results

## Getting Help

If you need help:
1. Check documentation
2. Search issues
3. Ask on Discord
4. Contact support

## Contributing

Want to help? See our [Contribution Guide](../CONTRIBUTION_GUIDE.md)
