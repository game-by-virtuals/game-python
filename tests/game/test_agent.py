"""Tests for the Agent module."""

import pytest
from unittest.mock import patch, MagicMock
from game_sdk.game.agent import Agent, Session
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import (
    Function,
    Argument,
    FunctionResult,
    FunctionResultStatus,
    ActionResponse,
    ActionType,
    AgentStateResponse
)
from game_sdk.game.exceptions import ValidationError


def test_session_initialization():
    """Test Session initialization."""
    session = Session()
    assert isinstance(session.id, str)
    assert session.function_result is None


def test_session_reset():
    """Test Session reset."""
    session = Session()
    original_id = session.id
    
    # Add a function result
    session.function_result = FunctionResult(
        action_id="test",
        action_status=FunctionResultStatus.DONE,
        feedback_message="Test",
        info={}
    )
    
    # Reset session
    session.reset()
    assert session.id != original_id
    assert session.function_result is None


def get_test_state(result, state):
    """Mock state function for testing."""
    return {"status": "ready"}


@patch('game_sdk.game.agent.create_agent')
def test_agent_initialization(mock_create_agent):
    """Test Agent initialization."""
    mock_create_agent.return_value = "test_agent_id"
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state
    )
    
    assert agent.name == "Test Agent"
    assert agent.agent_goal == "Test Goal"
    assert agent.agent_description == "Test Description"
    assert agent.agent_id == "test_agent_id"
    assert isinstance(agent._session, Session)
    assert agent.workers == {}
    assert agent.current_worker_id is None
    assert agent.agent_state == {"status": "ready"}
    
    mock_create_agent.assert_called_once_with(
        "https://api.virtuals.io",
        "test_key",
        "Test Agent",
        "Test Description",
        "Test Goal"
    )


def test_agent_initialization_no_api_key():
    """Test Agent initialization with no API key."""
    with pytest.raises(ValueError, match="API key not set"):
        Agent(
            api_key="",
            name="Test Agent",
            agent_goal="Test Goal",
            agent_description="Test Description",
            get_agent_state_fn=get_test_state
        )


def test_agent_initialization_invalid_state_fn():
    """Test Agent initialization with invalid state function."""
    def invalid_state_fn(result, state):
        return "not a dict"
    
    with pytest.raises(ValidationError, match="State function must return a dictionary"):
        Agent(
            api_key="test_key",
            name="Test Agent",
            agent_goal="Test Goal",
            agent_description="Test Description",
            get_agent_state_fn=invalid_state_fn
        )


@patch('game_sdk.game.agent.create_agent')
def test_agent_with_workers(mock_create_agent):
    """Test Agent initialization with workers."""
    mock_create_agent.return_value = "test_agent_id"
    
    worker_config = WorkerConfig(
        worker_name="Test Worker",
        worker_description="Test Worker Description",
        functions=[]
    )
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state,
        workers=[worker_config]
    )
    
    assert len(agent.workers) == 1
    assert worker_config.id in agent.workers
    assert agent.workers[worker_config.id] == worker_config


@patch('game_sdk.game.agent.create_agent')
@patch('game_sdk.game.agent.create_workers')
def test_agent_compile(mock_create_workers, mock_create_agent):
    """Test agent compilation."""
    mock_create_agent.return_value = "test_agent_id"
    
    worker_config = WorkerConfig(
        worker_name="Test Worker",
        worker_description="Test Worker Description",
        functions=[]
    )
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state,
        workers=[worker_config]
    )
    
    agent.compile()
    mock_create_workers.assert_called_once_with(
        "https://api.virtuals.io",
        "test_key",
        [worker_config]
    )


@patch('game_sdk.game.agent.create_agent')
def test_agent_compile_no_workers(mock_create_agent):
    """Test agent compilation with no workers."""
    mock_create_agent.return_value = "test_agent_id"
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state
    )
    
    with pytest.raises(ValueError, match="No workers configured"):
        agent.compile()


@patch('game_sdk.game.agent.create_agent')
def test_agent_reset(mock_create_agent):
    """Test agent reset."""
    mock_create_agent.return_value = "test_agent_id"
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state
    )
    
    original_session_id = agent._session.id
    agent.reset()
    assert agent._session.id != original_session_id


@patch('game_sdk.game.agent.create_agent')
def test_agent_add_worker(mock_create_agent):
    """Test adding a worker to an agent."""
    mock_create_agent.return_value = "test_agent_id"
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state
    )
    
    worker_config = WorkerConfig(
        worker_name="Test Worker",
        worker_description="Test Worker Description",
        functions=[]
    )
    
    workers = agent.add_worker(worker_config)
    assert len(workers) == 1
    assert worker_config.id in workers
    assert workers[worker_config.id] == worker_config


@patch('game_sdk.game.agent.create_agent')
def test_agent_get_worker_config(mock_create_agent):
    """Test getting a worker configuration."""
    mock_create_agent.return_value = "test_agent_id"
    
    worker_config = WorkerConfig(
        worker_name="Test Worker",
        worker_description="Test Worker Description",
        functions=[]
    )
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state,
        workers=[worker_config]
    )
    
    retrieved_config = agent.get_worker_config(worker_config.id)
    assert retrieved_config == worker_config


@patch('game_sdk.game.agent.create_agent')
def test_agent_get_worker(mock_create_agent):
    """Test getting a worker instance."""
    mock_create_agent.return_value = "test_agent_id"
    
    worker_config = WorkerConfig(
        worker_name="Test Worker",
        worker_description="Test Worker Description",
        functions=[]
    )
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state,
        workers=[worker_config]
    )
    
    worker = agent.get_worker(worker_config.id)
    assert worker.config == worker_config


@patch('game_sdk.game.agent.create_agent')
@patch('game_sdk.game.agent.post')
def test_agent_get_action(mock_post, mock_create_agent):
    """Test getting next action from API."""
    mock_create_agent.return_value = "test_agent_id"
    mock_post.return_value = ActionResponse(
        action_type=ActionType.CALL_FUNCTION,
        agent_state=AgentStateResponse(),
        action_args={}
    ).model_dump()
    
    agent = Agent(
        api_key="test_key",
        name="Test Agent",
        agent_goal="Test Goal",
        agent_description="Test Description",
        get_agent_state_fn=get_test_state
    )
    
    action = agent._get_action()
    assert isinstance(action, ActionResponse)
    assert action.action_type == ActionType.CALL_FUNCTION
    
    mock_post.assert_called_once_with(
        "https://api.virtuals.io",
        "test_key",
        endpoint="/v2/actions",
        data={
            "agent_id": "test_agent_id",
            "session_id": agent._session.id,
            "state": {"status": "ready"},
            "function_result": None
        }
    )
