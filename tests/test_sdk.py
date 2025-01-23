"""Tests for the GameSDK class."""
import pytest
from game_sdk.hosted_game.sdk import GameSDK

def test_gamesdk_initialization(mock_api_key):
    """Test GameSDK initialization with API key."""
    sdk = GameSDK(mock_api_key)
    assert sdk.api_key == mock_api_key
    assert sdk.api_url == "https://game-api.virtuals.io/api"

def test_gamesdk_functions(mock_api_key, mock_requests):
    """Test GameSDK functions method."""
    sdk = GameSDK(mock_api_key)
    mock_requests.get.return_value.json.return_value = {
        "data": [
            {"fn_name": "test_function", "fn_description": "Test function description"}
        ]
    }
    
    functions = sdk.functions()
    assert isinstance(functions, dict)
    assert "test_function" in functions
    assert functions["test_function"] == "Test function description"
    
    # Verify API call
    mock_requests.get.assert_called_once_with(
        f"{sdk.api_url}/functions",
        headers={"x-api-key": mock_api_key}
    )

def test_gamesdk_functions_error(mock_api_key, mock_requests):
    """Test GameSDK functions method error handling."""
    sdk = GameSDK(mock_api_key)
    mock_requests.get.return_value.status_code = 400
    mock_requests.get.return_value.json.return_value = {"error": "Bad Request"}
    
    with pytest.raises(Exception):
        sdk.functions()

def test_gamesdk_simulate(mock_api_key, mock_requests):
    """Test GameSDK simulate method."""
    sdk = GameSDK(mock_api_key)
    session_id = "test-session"
    goal = "test goal"
    description = "test description"
    world_info = "test world info"
    functions = []
    custom_functions = []
    
    # Mock both response and data field
    mock_response_data = {"status": "success"}
    mock_requests.post.return_value.json.return_value = {"data": mock_response_data}
    
    result = sdk.simulate(
        session_id=session_id,
        goal=goal,
        description=description,
        world_info=world_info,
        functions=functions,
        custom_functions=custom_functions
    )
    
    assert result == mock_response_data
    mock_requests.post.assert_called_once_with(
        f"{sdk.api_url}/simulate",
        json={"data": {
            "sessionId": session_id,
            "goal": goal,
            "description": description,
            "worldInfo": world_info,
            "functions": functions,
            "customFunctions": custom_functions,
        }},
        headers={"x-api-key": mock_api_key}
    )
