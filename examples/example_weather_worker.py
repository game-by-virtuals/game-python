"""
Example Weather Worker for the GAME SDK.

This module demonstrates how to create a standalone worker that provides weather
information and recommendations. It shows how to:

1. Define a worker's action space with custom functions
2. Handle API responses and errors gracefully
3. Provide helpful clothing recommendations
4. Maintain clean and testable code structure

The weather worker supports:
- Getting current weather conditions
- Providing temperature in Celsius
- Suggesting appropriate clothing
- Handling multiple cities

Example:
    >>> from game_sdk.game.worker_config import WorkerConfig
    >>> from game_sdk.game.worker import Worker
    >>> 
    >>> worker_config = create_weather_worker_config("your_api_key")
    >>> worker = Worker(worker_config)
    >>> result = worker.execute_function("get_weather", {"city": "New York"})
    >>> print(result["message"])
    'Current weather in New York: Sunny, 15°C, 60% humidity'

Note:
    This example uses a mock weather API for demonstration. In a production
    environment, you would want to use a real weather service API.
"""

import logging
from typing import Dict, Any, Optional
import requests
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import Function, Argument

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_weather(city: str) -> Dict[str, Any]:
    """Get weather information for a given city.
    
    This function makes an API call to fetch current weather data and provides
    clothing recommendations based on the temperature and conditions.
    
    Args:
        city (str): Name of the city to get weather for
        
    Returns:
        Dict[str, Any]: Weather information including:
            - status: API call status ('success' or 'error')
            - message: Human-readable weather description
            - data: Detailed weather information including:
                - city: City name
                - temperature: Temperature in Celsius
                - condition: Weather condition (e.g., 'Sunny', 'Cloudy')
                - humidity: Humidity percentage
                - clothing: Recommended clothing based on conditions
            
    Raises:
        requests.RequestException: If the API call fails
        
    Example:
        >>> result = get_weather("New York")
        >>> print(result["data"]["clothing"])
        'Light jacket'
    """
    try:
        # Make API call (using mock API for example)
        response = requests.get('https://dylanburkey.com/assets/weather.json')
        response.raise_for_status()
        
        # Process weather data (mock data for example)
        weather_data = {
            'New York': {'temp': '15°C', 'condition': 'Sunny', 'humidity': '60%'},
            'Miami': {'temp': '28°C', 'condition': 'Sunny', 'humidity': '70%'},
            'Boston': {'temp': '10°C', 'condition': 'Cloudy', 'humidity': '65%'}
        }.get(city, {'temp': '20°C', 'condition': 'Clear', 'humidity': '50%'})
        
        # Get temperature as number for clothing recommendation
        temp = int(weather_data['temp'].rstrip('°C'))
        
        # Determine appropriate clothing
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

def get_worker_state(function_result: Optional[Dict], current_state: Optional[Dict]) -> Dict[str, Any]:
    """Get the current state of the weather worker.
    
    This function maintains the worker's state between function calls,
    tracking the number of requests and their outcomes.
    
    Args:
        function_result: Result of the last executed function
        current_state: Current worker state
        
    Returns:
        Dict[str, Any]: Updated worker state including:
            - requests: Total number of requests made
            - successes: Number of successful requests
            - failures: Number of failed requests
            
    Example:
        >>> state = get_worker_state(None, None)
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

def create_weather_worker_config(api_key: str) -> WorkerConfig:
    """Create a configuration for the weather worker.
    
    This function sets up a WorkerConfig object that defines the worker's
    behavior, available actions, and state management.
    
    Args:
        api_key (str): API key for worker authentication
        
    Returns:
        WorkerConfig: Configured weather worker
        
    Example:
        >>> config = create_weather_worker_config("your_api_key")
        >>> print(config.worker_description)
        'Provides weather information and clothing recommendations'
    """
    # Create weather function
    weather_fn = Function(
        fn_name="get_weather",
        fn_description="Get weather information and recommendations for a city",
        executable=get_weather,
        args=[
            Argument(
                name="city",
                type="string",
                description="City to get weather for (e.g., New York, Miami, Boston)"
            )
        ]
    )
    
    # Create and return worker config
    return WorkerConfig(
        id="weather_worker",
        worker_description="Provides weather information and clothing recommendations",
        get_state_fn=get_worker_state,
        action_space=[weather_fn],
        instruction="Fetch weather data and provide appropriate clothing recommendations",
        api_key=api_key
    )

def main():
    """Run the weather worker example."""
    try:
        # Get API key from environment
        api_key = os.getenv("VIRTUALS_API_KEY")
        if not api_key:
            raise ValueError("VIRTUALS_API_KEY environment variable not set")

        # Create the agent
        agent = Agent(
            api_key=api_key,
            name="Weather Assistant",
            agent_goal="provide weather information and recommendations",
            agent_description="A helpful weather assistant that provides weather information and clothing recommendations",
            get_agent_state_fn=lambda x, y: {"status": "ready"}
        )

        # Add the weather worker
        worker_config = create_weather_worker_config(api_key)
        agent.add_worker(worker_config)
        agent.compile()

        # Example: Test the worker with a query
        logger.info("🌤️ Testing weather worker...")
        worker = agent.get_worker(worker_config.id)
        
        # Test with New York
        result = worker.execute_function(
            "get_weather",
            {"city": "New York"}
        )

        if result:
            logger.info("✅ Worker response received")
            logger.info(f"Response: {result}")
        else:
            logger.error("❌ No response received from worker")

    except Exception as e:
        logger.error(f"❌ Error running weather worker: {e}")
        raise

if __name__ == "__main__":
    main()
