"""
Test module for the weather worker functionality.
"""

import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime

from game_sdk.game.agent import Agent
from game_sdk.game.custom_types import FunctionResult, FunctionResultStatus
from examples.weather_worker import create_weather_worker, get_weather_handler

class TestWeatherWorker(unittest.TestCase):
    """Test cases for the weather worker functionality."""
    
    @patch('game_sdk.game.utils.post')
    def setUp(self, mock_post):
        """Set up test fixtures before each test method."""
        # Mock API responses
        mock_post.return_value = {"id": "test_agent_id"}
        
        # Mock API key for testing
        self.api_key = "test_api_key"
        
        # Create a mock agent
        self.agent = Agent(
            api_key=self.api_key,
            name="Test Weather Assistant",
            agent_description="Test weather reporter",
            agent_goal="Test weather reporting functionality",
            get_agent_state_fn=lambda x, y: {"status": "ready"}
        )
        
        # Create and add the weather worker
        self.worker_config = create_weather_worker(self.api_key)
        self.agent.add_worker(self.worker_config)

    def test_worker_creation(self):
        """Test if worker is created correctly."""
        self.assertIsNotNone(self.worker_config)
        self.assertTrue(self.worker_config.id.startswith("weather_reporter_"))
        
        # Check action space
        actions = {fn.fn_name: fn for fn in self.worker_config.action_space}
        self.assertIn("get_weather", actions)
        
        # Check get_weather function
        get_weather = actions["get_weather"]
        self.assertEqual(len(get_weather.args), 1)
        self.assertEqual(get_weather.args[0].name, "query")

    @patch('requests.get')
    def test_get_weather_success(self, mock_get):
        """Test successful weather retrieval."""
        # Mock weather API response
        mock_weather_data = {
            "weather": [
                {
                    "location": "New York",
                    "temperature": 72,
                    "condition": "sunny",
                    "humidity": 45,
                    "clothing": "light jacket"
                }
            ]
        }
        mock_get.return_value.json.return_value = mock_weather_data
        mock_get.return_value.raise_for_status.return_value = None
        
        # Test the handler
        result = get_weather_handler("What's the weather like in New York?")
        
        # Verify results
        self.assertEqual(result["status"], "success")
        self.assertIn("New York", result["message"])
        self.assertEqual(result["data"]["temperature"], 72)
        self.assertEqual(result["data"]["condition"], "sunny")
        self.assertEqual(result["data"]["humidity"], 45)
        self.assertEqual(result["data"]["clothing"], "light jacket")

    @patch('requests.get')
    def test_get_weather_invalid_city(self, mock_get):
        """Test handling of invalid city."""
        # Mock weather API response
        mock_weather_data = {"weather": []}
        mock_get.return_value.json.return_value = mock_weather_data
        mock_get.return_value.raise_for_status.return_value = None
        
        # Test the handler
        result = get_weather_handler("What's the weather like in InvalidCity?")
        
        # Verify results
        self.assertEqual(result["status"], "error")
        self.assertIn("No weather data available", result["message"])
        self.assertIn("error", result)

    @patch('requests.get')
    def test_get_weather_api_error(self, mock_get):
        """Test handling of API errors."""
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        # Test the handler
        result = get_weather_handler("What's the weather like in New York?")
        
        # Verify results
        self.assertEqual(result["status"], "error")
        self.assertIn("Failed to fetch weather data", result["message"])
        self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()
