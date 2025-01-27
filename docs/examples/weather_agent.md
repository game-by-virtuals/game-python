# Weather Agent Example

This example demonstrates how to create a weather agent using the GAME SDK. It showcases several key features of the SDK and serves as a practical guide for building your own agents.

## Overview

The weather agent example consists of three main components:

1. **Weather Agent** (`example_weather_agent.py`): The main agent that coordinates weather-related tasks
2. **Weather Worker** (`example_weather_worker.py`): A worker that handles weather data fetching and processing
3. **Worker Configuration** (`worker_config.py`): Configuration for the weather worker

## Features

- Fetch weather data for different cities
- Provide clothing recommendations based on temperature
- Handle API errors gracefully
- Track request statistics
- Comprehensive test suite

## Prerequisites

Before running the example, you'll need:

1. A Virtuals API key (set as `VIRTUALS_API_KEY` environment variable)
2. Python 3.9 or later
3. Required packages installed (see `requirements.txt`)

## Quick Start

```bash
# Set your API key
export VIRTUALS_API_KEY="your_api_key"

# Run the example
python examples/example_weather_agent.py
```

## Code Structure

### Weather Agent (`example_weather_agent.py`)

The main agent file that sets up and coordinates the weather worker:

```python
from game_sdk.game.agent import Agent
from game_sdk.game.worker_config import WorkerConfig

# Create and configure the agent
agent = create_weather_agent()

# Run tests
test_weather_agent(agent)
```

### Weather Worker (`example_weather_worker.py`)

The worker that handles weather-related tasks:

```python
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.worker import Worker

# Create worker configuration
config = create_weather_worker_config(api_key)

# Create worker instance
worker = Worker(config)

# Execute weather function
result = worker.execute_function("get_weather", {"city": "New York"})
```

## Key Concepts

### Worker Configuration

The worker is configured using a `WorkerConfig` object that defines:

1. Available functions (action space)
2. State management
3. Worker description and instructions

```python
worker_config = WorkerConfig(
    id="weather_worker",
    worker_description="Provides weather information and recommendations",
    get_state_fn=get_state,
    action_space=[weather_fn],
    instruction="Fetch weather data and provide recommendations"
)
```

### State Management

The worker maintains state between function calls:

```python
def get_state(function_result, current_state):
    if current_state is None:
        return {'requests': 0, 'successes': 0, 'failures': 0}
        
    if function_result and function_result.get('status') == 'success':
        current_state['successes'] += 1
    elif function_result:
        current_state['failures'] += 1
        
    current_state['requests'] += 1
    return current_state
```

### Error Handling

The example demonstrates proper error handling:

```python
try:
    response = requests.get('https://weather-api.com/data')
    response.raise_for_status()
    # Process response...
except requests.RequestException as e:
    logger.error(f"Failed to get weather: {e}")
    return {
        'status': 'error',
        'message': f"Failed to get weather for {city}",
        'data': None
    }
```

## Testing

The example includes comprehensive tests:

```python
def test_weather_agent(agent):
    test_cases = ["New York", "Miami", "Boston"]
    
    for city in test_cases:
        worker = agent.get_worker("weather_worker")
        result = worker.execute_function("get_weather", {"city": city})
        
        # Verify result
        assert result['status'] == 'success'
        assert 'temperature' in result['data']
        assert 'clothing' in result['data']
