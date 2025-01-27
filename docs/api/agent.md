# Agent

The `Agent` class is the high-level planner in the GAME SDK. It coordinates workers and manages the overall agent state.

## Overview

An agent is responsible for:
1. Managing multiple workers
2. Creating and tracking tasks
3. Making high-level decisions
4. Maintaining session state

## Basic Usage

Here's how to create and use an agent:

```python
from game_sdk.game.agent import Agent
from game_sdk.game.worker_config import WorkerConfig

# Create agent
agent = Agent(
    goal="Handle weather reporting",
    description="A weather reporting system"
)

# Add worker
worker_config = create_worker_config()
agent.add_worker(worker_config)

# Compile and run
agent.compile()
agent.run()
```

## Components

### Goal

The agent's primary objective:

```python
goal="Provide accurate weather information and recommendations"
```

### Description

Detailed description of the agent's purpose and capabilities:

```python
description="""
This agent:
1. Reports weather conditions
2. Provides clothing recommendations
3. Tracks weather patterns
"""
```

### Workers

Add workers to handle specific tasks:

```python
# Add multiple workers
agent.add_worker(weather_worker_config)
agent.add_worker(recommendation_worker_config)
agent.add_worker(analytics_worker_config)
```

## Best Practices

### 1. Clear Goals

Set specific, measurable goals:

```python
# Good
goal="Provide hourly weather updates for specified cities"

# Bad
goal="Handle weather stuff"
```

### 2. Detailed Descriptions

Provide comprehensive descriptions:

```python
description="""
Weather reporting agent that:
1. Monitors weather conditions
2. Provides clothing recommendations
3. Tracks temperature trends
4. Alerts on severe weather
"""
```

### 3. Worker Organization

Organize workers by function:

```python
# Weather monitoring
agent.add_worker(weather_monitor_config)

# Recommendations
agent.add_worker(clothing_advisor_config)

# Analytics
agent.add_worker(trend_analyzer_config)
```

### 4. Error Handling

Handle errors at the agent level:

```python
try:
    agent.compile()
    agent.run()
except Exception as e:
    logger.error(f"Agent error: {e}")
    # Handle error appropriately
```

## Examples

### Weather Agent

```python
def create_weather_agent():
    """Create a weather reporting agent."""
    # Create agent
    agent = Agent(
        goal="Provide weather updates and recommendations",
        description="""
        Weather reporting system that:
        1. Monitors current conditions
        2. Provides clothing recommendations
        3. Tracks weather patterns
        """
    )
    
    # Add workers
    agent.add_worker(create_weather_worker_config())
    agent.add_worker(create_recommendation_worker_config())
    
    return agent
```

### Task Manager

```python
def create_task_manager():
    """Create a task management agent."""
    # Create agent
    agent = Agent(
        goal="Manage and track tasks efficiently",
        description="""
        Task management system that:
        1. Creates and assigns tasks
        2. Tracks task progress
        3. Generates reports
        """
    )
    
    # Add workers
    agent.add_worker(create_task_worker_config())
    agent.add_worker(create_report_worker_config())
    
    return agent
```

## Testing

Test your agents thoroughly:

```python
def test_weather_agent():
    """Test weather agent functionality."""
    # Create agent
    agent = create_weather_agent()
    
    # Test worker addition
    assert len(agent.workers) > 0
    
    # Test compilation
    agent.compile()
    assert agent.is_compiled
    
    # Test execution
    result = agent.run()
    assert result.status == 'success'
```

## Advanced Features

### 1. Session Management

```python
# Start new session
session = agent.start_session()

# Resume existing session
agent.resume_session(session_id)
```

### 2. State Tracking

```python
# Get agent state
state = agent.get_state()

# Update state
agent.update_state(new_state)
```

### 3. Worker Communication

```python
# Get worker results
results = agent.get_worker_results()

# Share data between workers
agent.share_data(worker1_id, worker2_id, data)
```

## Common Issues

1. **Worker Conflicts**
   - Ensure workers have unique IDs
   - Define clear worker responsibilities
   - Handle shared resources properly

2. **State Management**
   - Keep state minimal
   - Handle state updates atomically
   - Document state structure

3. **Performance**
   - Monitor worker execution time
   - Optimize resource usage
   - Cache frequently used data

## Further Reading

- [Worker Documentation](worker.md)
- [Worker Configuration](worker_config.md)
- [Examples](../examples/)
