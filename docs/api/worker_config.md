# Worker Configuration

The `WorkerConfig` class is a fundamental component of the GAME SDK that defines how a worker behaves. This document explains how to create and use worker configurations effectively.

## Overview

A worker configuration defines:

1. The worker's identity and description
2. Available actions (functions) that the worker can perform
3. State management behavior
4. Instructions for the worker

## Basic Usage

Here's a simple example of creating a worker configuration:

```python
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import Function, Argument

# Define a function
my_function = Function(
    fn_name="my_function",
    fn_description="Does something useful",
    executable=my_function_handler,
    args=[
        Argument(
            name="param1",
            type="string",
            description="First parameter"
        )
    ]
)

# Create configuration
config = WorkerConfig(
    id="my_worker",
    worker_description="A useful worker",
    get_state_fn=get_state_handler,
    action_space=[my_function],
    instruction="Do something useful"
)
```

## Components

### Worker ID

A unique identifier for the worker. This should be:
- Descriptive of the worker's purpose
- Unique within your agent
- Valid Python identifier (no spaces or special characters)

```python
id="weather_worker"  # Good
id="weather-worker"  # Bad (contains hyphen)
```

### Worker Description

A clear description of what the worker does. This should:
- Explain the worker's purpose
- List key capabilities
- Be concise but informative

```python
worker_description="Provides weather information and clothing recommendations"
```

### State Management

The `get_state_fn` defines how the worker maintains state between function calls:

```python
def get_state(function_result, current_state):
    """Manage worker state.
    
    Args:
        function_result: Result of last function call
        current_state: Current state dictionary
        
    Returns:
        Updated state dictionary
    """
    if current_state is None:
        return {'count': 0}
        
    current_state['count'] += 1
    return current_state
```

### Action Space

The `action_space` defines what functions the worker can perform:

```python
action_space=[
    Function(
        fn_name="function1",
        fn_description="Does something",
        executable=handler1,
        args=[...]
    ),
    Function(
        fn_name="function2",
        fn_description="Does something else",
        executable=handler2,
        args=[...]
    )
]
```

### Instructions

Clear instructions for the worker:

```python
instruction="""
This worker can:
1. Do something useful
2. Handle specific tasks
3. Process certain data
"""
```

## Best Practices

1. **Clear Documentation**
   - Document all functions thoroughly
   - Include usage examples
   - Explain parameters clearly

2. **Error Handling**
   - Handle errors gracefully in function handlers
   - Return meaningful error messages
   - Log errors appropriately

3. **State Management**
   - Keep state minimal and focused
   - Handle None state appropriately
   - Document state structure

4. **Testing**
   - Test all functions thoroughly
   - Verify error handling
   - Check state management

## Examples

### Weather Worker

```python
def create_weather_worker_config(api_key: str) -> WorkerConfig:
    """Create weather worker configuration.
    
    Args:
        api_key: API key for authentication
        
    Returns:
        Configured WorkerConfig
    """
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
    
    return WorkerConfig(
        id="weather_worker",
        worker_description="Weather information system",
        get_state_fn=get_state,
        action_space=[weather_fn],
        instruction="Fetch weather data"
    )
```

### Task Worker

```python
def create_task_worker_config() -> WorkerConfig:
    """Create task management worker configuration."""
    add_task = Function(
        fn_name="add_task",
        fn_description="Add a new task",
        executable=add_task_handler,
        args=[
            Argument(
                name="title",
                type="string",
                description="Task title"
            ),
            Argument(
                name="priority",
                type="integer",
                description="Task priority (1-5)"
            )
        ]
    )
    
    return WorkerConfig(
        id="task_worker",
        worker_description="Task management system",
        get_state_fn=get_task_state,
        action_space=[add_task],
        instruction="Manage tasks"
    )
```
