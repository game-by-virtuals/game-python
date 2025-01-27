"""
Tests for custom types and data structures in the GAME SDK.

This module contains comprehensive tests for all custom types defined in
game_sdk.game.custom_types.
"""

import pytest
from typing import Dict, Any
from game_sdk.game.custom_types import (
    Argument,
    Function,
    FunctionResult,
    FunctionResultStatus,
    ActionType,
    HLPResponse,
    LLPResponse,
    CurrentTaskResponse,
    AgentStateResponse,
    ActionResponse
)


def test_argument_creation():
    """Test creating an Argument with various configurations."""
    # Test required fields
    arg = Argument(
        name="city",
        description="City name",
        type="string"
    )
    assert arg.name == "city"
    assert arg.description == "City name"
    assert arg.type == "string"
    assert not arg.optional

    # Test optional argument
    optional_arg = Argument(
        name="country",
        description="Country name",
        type="string",
        optional=True
    )
    assert optional_arg.optional

    # Test list type
    multi_type_arg = Argument(
        name="temperature",
        description="Temperature value",
        type=["integer", "float"]
    )
    assert isinstance(multi_type_arg.type, list)
    assert "integer" in multi_type_arg.type
    assert "float" in multi_type_arg.type


def test_function_result_status():
    """Test FunctionResultStatus enum values."""
    assert FunctionResultStatus.DONE == "done"
    assert FunctionResultStatus.FAILED == "failed"
    
    # Test string conversion
    assert str(FunctionResultStatus.DONE) == "done"
    assert str(FunctionResultStatus.FAILED) == "failed"


def test_function_result():
    """Test FunctionResult creation and attributes."""
    result = FunctionResult(
        action_id="test_123",
        action_status=FunctionResultStatus.DONE,
        feedback_message="Test completed",
        info={"value": 42}
    )
    
    assert result.action_id == "test_123"
    assert result.action_status == FunctionResultStatus.DONE
    assert result.feedback_message == "Test completed"
    assert result.info == {"value": 42}


def get_test_value(value: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function for testing."""
    return FunctionResultStatus.DONE, f"Got value: {value['value']}", {"value": value['value']}


def test_function():
    """Test Function creation and execution."""
    # Create test function
    fn = Function(
        fn_name="get_value",
        fn_description="Get a value",
        args=[
            Argument(
                name="value",
                description="Value to get",
                type="string"
            )
        ],
        executable=get_test_value
    )
    
    # Test function definition
    assert fn.fn_name == "get_value"
    assert fn.fn_description == "Get a value"
    assert len(fn.args) == 1
    
    # Test function execution
    result = fn.execute(
        fn_id="test_123",
        args={"value": {"value": "test"}}
    )
    assert result.action_status == FunctionResultStatus.DONE
    assert result.info == {"value": "test"}
    
    # Test error handling
    result = fn.execute(
        fn_id="test_456",
        args={"invalid": "value"}
    )
    assert result.action_status == FunctionResultStatus.FAILED
    assert "Error executing function" in result.feedback_message


def test_action_type():
    """Test ActionType enum values."""
    assert ActionType.CALL_FUNCTION == "call_function"
    assert ActionType.CONTINUE_FUNCTION == "continue_function"
    assert ActionType.WAIT == "wait"
    assert ActionType.GO_TO == "go_to"


def test_hlp_response():
    """Test HLPResponse creation and attributes."""
    hlp = HLPResponse(
        plan_id="test_123",
        observation_reflection="Test reflection",
        plan=["step1", "step2"],
        plan_reasoning="Test reasoning",
        current_state_of_execution="Running",
        change_indicator="Changed",
        log=[{"event": "start"}]
    )
    
    assert hlp.plan_id == "test_123"
    assert hlp.observation_reflection == "Test reflection"
    assert len(hlp.plan) == 2
    assert hlp.plan_reasoning == "Test reasoning"
    assert hlp.current_state_of_execution == "Running"
    assert hlp.change_indicator == "Changed"
    assert len(hlp.log) == 1


def test_llp_response():
    """Test LLPResponse creation and attributes."""
    llp = LLPResponse(
        plan_id="test_123",
        plan_reasoning="Test reasoning",
        situation_analysis="Test analysis",
        plan=["step1", "step2"],
        change_indicator="Changed",
        reflection="Test reflection"
    )
    
    assert llp.plan_id == "test_123"
    assert llp.plan_reasoning == "Test reasoning"
    assert llp.situation_analysis == "Test analysis"
    assert len(llp.plan) == 2
    assert llp.change_indicator == "Changed"
    assert llp.reflection == "Test reflection"


def test_current_task_response():
    """Test CurrentTaskResponse creation and attributes."""
    llp = LLPResponse(
        plan_id="test_123",
        plan_reasoning="Test reasoning",
        situation_analysis="Test analysis",
        plan=["step1"]
    )
    
    task = CurrentTaskResponse(
        task="Test task",
        task_reasoning="Test reasoning",
        location_id="test_loc",
        llp=llp
    )
    
    assert task.task == "Test task"
    assert task.task_reasoning == "Test reasoning"
    assert task.location_id == "test_loc"
    assert task.llp == llp


def test_agent_state_response():
    """Test AgentStateResponse creation and attributes."""
    hlp = HLPResponse(
        plan_id="test_123",
        observation_reflection="Test reflection",
        plan=["step1"],
        plan_reasoning="Test reasoning",
        current_state_of_execution="Running"
    )
    
    task = CurrentTaskResponse(
        task="Test task",
        task_reasoning="Test reasoning"
    )
    
    state = AgentStateResponse(
        hlp=hlp,
        current_task=task
    )
    
    assert state.hlp == hlp
    assert state.current_task == task


def test_action_response():
    """Test ActionResponse creation and attributes."""
    state = AgentStateResponse()
    
    response = ActionResponse(
        action_type=ActionType.CALL_FUNCTION,
        agent_state=state,
        action_args={"function": "test"}
    )
    
    assert response.action_type == ActionType.CALL_FUNCTION
    assert response.agent_state == state
    assert response.action_args == {"function": "test"}
