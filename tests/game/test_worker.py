"""Tests for the Worker class."""

import pytest
from game_sdk.game.worker import Worker
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import (
    Function,
    Argument,
    FunctionResult,
    FunctionResultStatus
)


def test_worker_initialization():
    """Test worker initialization with config."""
    config = WorkerConfig(
        worker_name="test_worker",
        worker_description="Test worker",
        functions=[],
        state={"initial": "state"}
    )
    worker = Worker(config)
    assert worker.config == config
    assert worker.state == {"initial": "state"}


def test_worker_initialization_default_state():
    """Test worker initialization with default state."""
    config = WorkerConfig(
        worker_name="test_worker",
        worker_description="Test worker",
        functions=[]
    )
    worker = Worker(config)
    assert worker.config == config
    assert worker.state == {}


def test_execute_function_not_found():
    """Test executing a non-existent function."""
    config = WorkerConfig(
        worker_name="test_worker",
        worker_description="Test worker",
        functions=[]
    )
    worker = Worker(config)
    result = worker.execute_function("nonexistent", "123", {})
    
    assert isinstance(result, dict)
    assert "result" in result
    assert "state" in result
    assert result["result"].action_id == "123"
    assert result["result"].action_status == FunctionResultStatus.FAILED
    assert "not found" in result["result"].feedback_message


def test_execute_function_success():
    """Test successful function execution."""
    def test_fn(**kwargs):
        return FunctionResultStatus.DONE, "Success", {"output": "test"}

    fn = Function(
        fn_name="test_fn",
        fn_description="Test function",
        args=[
            Argument(
                name="input",
                description="Test input",
                type="string"
            )
        ],
        executable=test_fn
    )

    config = WorkerConfig(
        worker_name="test_worker",
        worker_description="Test worker",
        functions=[fn]
    )
    worker = Worker(config)
    result = worker.execute_function("test_fn", "123", {"input": "test"})
    
    assert isinstance(result, dict)
    assert "result" in result
    assert "state" in result
    assert result["result"].action_id == "123"
    assert result["result"].action_status == FunctionResultStatus.DONE
    assert result["result"].feedback_message == "Success"
    assert result["result"].info == {"output": "test"}


def test_execute_function_error():
    """Test function execution with error."""
    def test_fn(**kwargs):
        raise ValueError("Test error")

    fn = Function(
        fn_name="test_fn",
        fn_description="Test function",
        args=[],
        executable=test_fn
    )

    config = WorkerConfig(
        worker_name="test_worker",
        worker_description="Test worker",
        functions=[fn]
    )
    worker = Worker(config)
    result = worker.execute_function("test_fn", "123", {})
    
    assert isinstance(result, dict)
    assert "result" in result
    assert "state" in result
    assert result["result"].action_id == "123"
    assert result["result"].action_status == FunctionResultStatus.FAILED
    assert "Test error" in result["result"].feedback_message


def test_update_state():
    """Test state updates after function execution."""
    config = WorkerConfig(
        worker_name="test_worker",
        worker_description="Test worker",
        functions=[],
        state={"initial": "state"}
    )
    worker = Worker(config)
    
    result = FunctionResult(
        action_id="123",
        action_status=FunctionResultStatus.DONE,
        feedback_message="Success",
        info={"output": "test"}
    )
    
    new_state = worker._update_state(result)
    assert new_state["initial"] == "state"
    assert "last_result" in new_state
    assert new_state["last_result"]["action_id"] == "123"
