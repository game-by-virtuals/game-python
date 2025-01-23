"""Tests for the Worker class."""
import pytest
from unittest.mock import Mock, patch

from game_sdk.game.custom_types import Function, FunctionResult, FunctionResultStatus, ActionResponse, ActionType
from game_sdk.game.worker import Worker

@pytest.fixture
def mock_api_key():
    return "test-api-key-12345"

@pytest.fixture
def mock_get_state_fn():
    return Mock(return_value={"status": "active"})

@pytest.fixture
def mock_action_space():
    return [
        Function(
            fn_name="test_function",
            fn_description="Test function description",
            args=[],
            hint=None
        )
    ]

@pytest.fixture
def mock_utils():
    with patch("game_sdk.game.worker.create_agent") as mock_create_agent, \
         patch("game_sdk.game.worker.post") as mock_post:
        mock_create_agent.return_value = "test-agent-id"
        mock_post.return_value = {"submission_id": "test-submission-id"}
        yield {
            "create_agent": mock_create_agent,
            "post": mock_post
        }

def test_worker_initialization(mock_api_key, mock_get_state_fn, mock_action_space, mock_utils):
    """Test Worker initialization."""
    description = "Test worker description"
    instruction = "Test instruction"

    worker = Worker(
        api_key=mock_api_key,
        description=description,
        get_state_fn=mock_get_state_fn,
        action_space=mock_action_space,
        instruction=instruction
    )

    assert worker._api_key == mock_api_key
    assert worker.description == description
    assert worker.instruction == instruction
    assert worker._get_state_fn == mock_get_state_fn
    
    mock_utils["create_agent"].assert_called_once_with(
        api_key=mock_api_key,
        description=description,
        instruction=instruction
    )

def test_worker_initialization_no_api_key():
    """Test Worker initialization with no API key."""
    with pytest.raises(ValueError, match="API key not set"):
        Worker(
            api_key="",
            description="Test description",
            get_state_fn=lambda x, y: {},
            action_space=[]
        )

def test_worker_step_success(mock_api_key, mock_get_state_fn, mock_action_space, mock_utils):
    """Test successful Worker step."""
    worker = Worker(
        api_key=mock_api_key,
        description="Test description",
        get_state_fn=mock_get_state_fn,
        action_space=mock_action_space
    )

    # Set task first
    worker.set_task("Test task")

    # Mock API response for step
    mock_utils["post"].return_value = {
        "action_type": "call_function",
        "agent_state": {"current_task": None},
        "action_args": {
            "fn_name": "test_function",
            "fn_id": "test-fn-id"
        }
    }

    # Execute step
    action_response, function_result = worker.step()
    
    assert action_response.action_type == ActionType.CALL_FUNCTION
    assert action_response.action_args["fn_name"] == "test_function"
    assert function_result is not None
    assert function_result.action_id == "test-fn-id"

def test_worker_step_api_error(mock_api_key, mock_get_state_fn, mock_action_space, mock_utils):
    """Test Worker step with API error."""
    worker = Worker(
        api_key=mock_api_key,
        description="Test description",
        get_state_fn=mock_get_state_fn,
        action_space=mock_action_space
    )

    # Set task first
    worker.set_task("Test task")

    # Mock API error
    mock_utils["post"].side_effect = ValueError("API Error")

    # Execute step and expect exception
    with pytest.raises(ValueError, match="API Error"):
        worker.step()

def test_worker_step_with_function_result(mock_api_key, mock_get_state_fn, mock_action_space, mock_utils):
    """Test Worker step with previous function result."""
    worker = Worker(
        api_key=mock_api_key,
        description="Test description",
        get_state_fn=mock_get_state_fn,
        action_space=mock_action_space
    )

    # Set task first
    worker.set_task("Test task")

    # Create a function result
    function_result = FunctionResult(
        action_id="test_action",
        action_status=FunctionResultStatus.DONE,
        feedback_message="Test completed",
        info={"result": "success"}
    )

    # Mock API response
    mock_utils["post"].return_value = {
        "action_type": "call_function",
        "agent_state": {"current_task": None},
        "action_args": {"fn_name": "test_function"}
    }

    # Execute step with function result
    action_response = worker._get_action(function_result)
    
    # Verify the API was called with the correct data
    mock_utils["post"].assert_called_with(
        base_url="https://game.virtuals.io",
        api_key=mock_api_key,
        endpoint="/v2/agents/test-agent-id/tasks/test-submission-id/next",
        data={
            "environment": {"instructions": "", "status": "active"},
            "functions": [{
                "fn_name": "test_function",
                "fn_description": "Test function description",
                "args": [],
                "hint": None
            }],
            "action_result": {
                "action_id": "test_action",
                "action_status": "done",
                "feedback_message": "Test completed"
            }
        }
    )
