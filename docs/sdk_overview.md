# GAME SDK Overview

## Architecture

The GAME SDK is built on three main components:

1. **Agent (High Level Planner)**
   - Takes a Goal and Description
   - Creates and manages tasks
   - Coordinates multiple workers
   - Makes high-level decisions

2. **Worker (Low Level Planner)**
   - Takes a Description
   - Executes specific tasks
   - Manages state
   - Calls functions

3. **Function**
   - Takes a Description
   - Executes specific actions
   - Returns results
   - Handles errors

![New SDK Visual](imgs/new_sdk_visual.png)

## Key Features

- **Custom Agent Development**: Build agents for any application
- **Description-Based Control**: Control agents and workers via prompts
- **State Management**: Full control over agent state
- **Function Customization**: Create complex function chains
- **Error Handling**: Robust error handling throughout
- **Type Safety**: Strong typing for better development

## Component Descriptions

### Agent

The Agent serves as the high-level planner:

```python
from game_sdk.game.agent import Agent

agent = Agent(
    goal="Handle weather reporting",
    description="A weather reporting system that provides updates and recommendations"
)
```

### Worker

Workers handle specific tasks:

```python
from game_sdk.game.worker import Worker
from game_sdk.game.worker_config import WorkerConfig

worker_config = WorkerConfig(
    id="weather_worker",
    description="Provides weather information",
    action_space=[weather_function]
)

worker = Worker(worker_config)
```

### Function

Functions execute specific actions:

```python
from game_sdk.game.custom_types import Function, Argument

weather_function = Function(
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
```

## Best Practices

1. **Clear Documentation**
   - Document all components thoroughly
   - Include usage examples
   - Explain parameters clearly

2. **Error Handling**
   - Handle errors at all levels
   - Provide meaningful error messages
   - Log errors appropriately

3. **State Management**
   - Keep state minimal and focused
   - Handle state updates cleanly
   - Document state structure

4. **Testing**
   - Test all components
   - Cover error cases
   - Verify state management

## Examples

See the [examples](examples/) directory for complete examples:

- Weather Agent: Complete weather reporting system
- Task Manager: Task management system
- Twitter Bot: Social media interaction

## Getting Started

1. Install the SDK:
```bash
pip install game_sdk
```

2. Set up your API key:
```bash
export VIRTUALS_API_KEY="your_api_key"
```

3. Create your first agent:
```python
from game_sdk.game.agent import Agent
from game_sdk.game.worker import Worker

# Create agent
agent = Agent(
    goal="Your goal",
    description="Your description"
)

# Add workers
agent.add_worker(worker_config)

# Run agent
agent.run()
```

## Further Reading

- [API Documentation](api/)
- [Examples](examples/)
- [Contributing Guide](../CONTRIBUTION_GUIDE.md)
- [GAME Framework](https://whitepaper.virtuals.io/developer-documents/game-framework)
