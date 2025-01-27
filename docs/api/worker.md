# Worker Implementation

The `Worker` class is a core component of the GAME SDK that executes functions and manages state based on a worker configuration.

## Overview

A worker is responsible for:
1. Executing functions defined in its action space
2. Managing state between function calls
3. Handling errors and logging
4. Providing feedback on execution results

## Basic Usage

Here's how to create and use a worker:

```python
from game_sdk.game.worker import Worker
from game_sdk.game.worker_config import WorkerConfig

# Create worker configuration
config = create_worker_config()

# Create worker instance
worker = Worker(config)

# Execute a function
result = worker.execute_function(
    "function_name",
    {"param1": "value1"}
)
```

## Components

### Worker Configuration

A worker requires a `WorkerConfig` that defines its behavior:

```python
worker_config = WorkerConfig(
    id="my_worker",
    worker_description="Does something useful",
    get_state_fn=get_state,
    action_space=[function1, function2],
    instruction="Do something"
)
```

### Function Execution

Workers execute functions from their action space:

```python
# Execute with parameters
result = worker.execute_function(
    "get_weather",
    {"city": "New York"}
)

# Check result
if result['status'] == 'success':
    print(result['data'])
else:
    print(f"Error: {result['message']}")
```

### State Management

Workers maintain state between function calls:

```python
def get_state(function_result, current_state):
    """Update worker state after function execution."""
    if current_state is None:
        return {'requests': 0}
        
    current_state['requests'] += 1
    return current_state
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
def my_function(param1: str) -> Dict[str, Any]:
    try:
        # Do something
        return {
            'status': 'success',
            'message': 'Operation completed',
            'data': result
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'data': None
        }
```

### 2. Logging

Use appropriate logging levels:

```python
import logging

logger = logging.getLogger(__name__)

def my_function(param1: str):
    logger.info(f"Starting operation with {param1}")
    try:
        result = do_something(param1)
        logger.debug(f"Operation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
```

### 3. Type Hints

Use type hints for better code clarity:

```python
from typing import Dict, Any, Optional

def get_state(
    function_result: Optional[Dict[str, Any]],
    current_state: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Update worker state."""
    pass
```

### 4. Documentation

Document all functions thoroughly:

```python
def execute_function(
    self,
    function_name: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a function with given parameters.
    
    Args:
        function_name: Name of function to execute
        parameters: Function parameters
        
    Returns:
        Dict containing:
            - status: 'success' or 'error'
            - message: Human-readable message
            - data: Function result data
            
    Raises:
        ValueError: If function not found
    """
    pass
```

## Examples

### Weather Worker

```python
# Create weather worker
weather_config = create_weather_worker_config(api_key)
weather_worker = Worker(weather_config)

# Get weather
result = weather_worker.execute_function(
    "get_weather",
    {"city": "New York"}
)

# Process result
if result['status'] == 'success':
    weather = result['data']
    print(f"Temperature: {weather['temperature']}")
    print(f"Condition: {weather['condition']}")
    print(f"Recommendation: {weather['clothing']}")
else:
    print(f"Error: {result['message']}")
```

### Task Worker

```python
# Create task worker
task_config = create_task_worker_config()
task_worker = Worker(task_config)

# Add task
result = task_worker.execute_function(
    "add_task",
    {
        "title": "Complete documentation",
        "priority": 1
    }
)

# Check result
if result['status'] == 'success':
    print(f"Task added: {result['data']['task_id']}")
else:
    print(f"Failed to add task: {result['message']}")
```

## Testing

Test your workers thoroughly:

```python
def test_weather_worker():
    """Test weather worker functionality."""
    # Create worker
    config = create_weather_worker_config(test_api_key)
    worker = Worker(config)
    
    # Test valid city
    result = worker.execute_function(
        "get_weather",
        {"city": "New York"}
    )
    assert result['status'] == 'success'
    assert 'temperature' in result['data']
    
    # Test invalid city
    result = worker.execute_function(
        "get_weather",
        {"city": "NonexistentCity"}
    )
    assert result['status'] == 'error'
```
