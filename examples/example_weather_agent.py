"""
Example Weather Agent for the GAME SDK.

This script demonstrates how to create and test an agent that provides weather
information and recommendations using the GAME SDK. It showcases:

1. Creating a weather agent with a custom worker
2. Configuring the worker with weather-related functions
3. Testing the agent with different cities
4. Handling API responses and state management

The weather agent can:
- Fetch current weather for a given city
- Provide clothing recommendations based on weather
- Handle multiple cities in sequence

Example:
    $ export VIRTUALS_API_KEY="your_api_key"
    $ python examples/example_weather_agent.py

Note:
    This example requires a valid Virtuals API key to be set in the
    environment variable VIRTUALS_API_KEY.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import requests

from game_sdk.game.agent import Agent
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import Function, Argument
from game_sdk.game.exceptions import ValidationError, APIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_weather(city: str) -> Dict[str, Any]:
    """Get weather information for a given city.
    
    This function makes an API call to fetch current weather data
    and provides clothing recommendations based on conditions.
    
    Args:
        city (str): Name of the city to get weather for
        
    Returns:
        Dict[str, Any]: Weather information including:
            - status: API call status
            - message: Formatted weather message
            - data: Detailed weather data
            
    Raises:
        requests.RequestException: If the API call fails
        
    Example:
        >>> result = get_weather("New York")
        >>> print(result['message'])
        'Current weather in New York: Sunny, 15°C, 60% humidity'
    """
    try:
        # Simulate API call (replace with actual weather API in production)
        response = requests.get('https://dylanburkey.com/assets/weather.json')
        response.raise_for_status()
        
        # Process response
        weather_data = {
            'New York': {'temp': '15°C', 'condition': 'Sunny', 'humidity': '60%'},
            'Miami': {'temp': '28°C', 'condition': 'Sunny', 'humidity': '70%'},
            'Boston': {'temp': '10°C', 'condition': 'Cloudy', 'humidity': '65%'}
        }.get(city, {'temp': '20°C', 'condition': 'Clear', 'humidity': '50%'})
        
        # Determine clothing recommendation
        temp = int(weather_data['temp'].rstrip('°C'))
        if temp > 25:
            clothing = 'Shorts and t-shirt'
        elif temp > 15:
            clothing = 'Light jacket'
        else:
            clothing = 'Sweater'
            
        return {
            'status': 'success',
            'message': f"Current weather in {city}: {weather_data['condition']}, "
                      f"{weather_data['temp']}°F, {weather_data['humidity']} humidity",
            'data': {
                'city': city,
                'temperature': weather_data['temp'],
                'condition': weather_data['condition'],
                'humidity': weather_data['humidity'],
                'clothing': clothing
            }
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to get weather: {e}")
        return {
            'status': 'error',
            'message': f"Failed to get weather for {city}",
            'data': None
        }

def get_state(function_result: Optional[Dict], current_state: Optional[Dict]) -> Dict[str, Any]:
    """Get the current state of the weather agent.
    
    This function maintains the agent's state between function calls,
    tracking successful and failed requests.
    
    Args:
        function_result: Result of the last executed function
        current_state: Current agent state
        
    Returns:
        Dict[str, Any]: Updated agent state
        
    Example:
        >>> state = get_state(None, None)
        >>> print(state)
        {'requests': 0, 'successes': 0, 'failures': 0}
    """
    if current_state is None:
        return {'requests': 0, 'successes': 0, 'failures': 0}
        
    if function_result and function_result.get('status') == 'success':
        current_state['successes'] += 1
    elif function_result:
        current_state['failures'] += 1
        
    current_state['requests'] += 1
    return current_state

def create_weather_agent() -> Agent:
    """Create and configure a weather agent.
    
    This function sets up an agent with a weather worker that can
    fetch weather information and provide recommendations.
    
    Returns:
        Agent: Configured weather agent
        
    Raises:
        ValueError: If VIRTUALS_API_KEY is not set
        ValidationError: If worker configuration is invalid
        APIError: If agent creation fails
        
    Example:
        >>> agent = create_weather_agent()
        >>> agent.compile()
    """
    # Get API key
    api_key = os.getenv('VIRTUALS_API_KEY')
    if not api_key:
        raise ValueError("VIRTUALS_API_KEY not set")
    
    logger.debug("Starting weather reporter creation")
    logger.debug(f"Creating agent with API key: {api_key[:8]}...")
    
    # Create weather function
    weather_fn = Function(
        fn_name="get_weather",
        fn_description="Get weather information for a city",
        executable=get_weather,
        args=[
            Argument(
                name="city",
                type="string",
                description="City to get weather for"
            )
        ]
    )
    
    # Create worker config
    worker_config = WorkerConfig(
        id="weather_worker",
        worker_description="Provides weather information and recommendations",
        get_state_fn=get_state,
        action_space=[weather_fn],
        instruction="Fetch weather data and provide clothing recommendations",
        api_key=api_key
    )
    
    # Create agent
    agent = Agent(
        api_key=api_key,
        name="Weather Reporter",
        agent_description="Reports weather and provides recommendations",
        agent_goal="Help users prepare for weather conditions",
        get_agent_state_fn=get_state,
        workers=[worker_config]
    )
    
    # Compile agent
    agent.compile()
    logger.info("Created weather reporter agent")
    return agent

def test_weather_agent(agent: Agent):
    """Test the weather agent with different cities.
    
    This function runs a series of tests to verify that the agent
    can correctly fetch and process weather information.
    
    Args:
        agent (Agent): Weather agent to test
        
    Raises:
        AssertionError: If any test fails
        
    Example:
        >>> agent = create_weather_agent()
        >>> test_weather_agent(agent)
        ✨ All weather reporter tests passed!
    """
    logger.debug("Starting weather reporter tests")
    
    # Test cities
    test_cases = ["New York", "Miami", "Boston"]
    
    for city in test_cases:
        logger.info(f"\nExecuting: Getting weather for {city}")
        
        # Get worker
        worker = agent.get_worker("weather_worker")
        
        # Execute function
        result = worker.execute_function("get_weather", {"city": city})
        logger.info(f"Result: {result}")
        
        # Verify result
        assert result['status'] == 'success', f"Failed to get weather for {city}"
        assert result['data']['city'] == city, f"Wrong city in response"
        assert 'temperature' in result['data'], "No temperature in response"
        assert 'condition' in result['data'], "No condition in response"
        assert 'humidity' in result['data'], "No humidity in response"
        assert 'clothing' in result['data'], "No clothing recommendation"
        
        logger.info("✓ Test passed")
    
    logger.info("\n✨ All weather reporter tests passed!")

def main():
    """Main entry point for the weather agent example.
    
    This function creates a weather agent and runs tests to verify
    its functionality.
    
    Raises:
        ValueError: If VIRTUALS_API_KEY is not set
        ValidationError: If agent configuration is invalid
        APIError: If agent creation or API calls fail
    """
    try:
        # Create and test agent
        agent = create_weather_agent()
        test_weather_agent(agent)
        
    except Exception as e:
        logger.error(f"Error running weather agent: {e}")
        raise

if __name__ == "__main__":
    main()
