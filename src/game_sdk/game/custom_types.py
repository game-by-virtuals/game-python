"""Custom types and data structures for the GAME SDK.

This module defines core data structures and types used in the SDK."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from pydantic import BaseModel


class Argument(BaseModel):
    """Defines an argument for a function.

    Attributes:
        name: Name of the argument
        description: Description of what the argument does
        type: Type of the argument (string, integer, etc.)
        optional: Whether the argument is optional
    """
    name: str
    description: str
    type: Union[str, List[str]]
    optional: bool = False


class FunctionResultStatus(str, Enum):
    """Status of a function execution.

    Attributes:
        DONE: Function completed successfully
        FAILED: Function failed to complete
    """
    DONE = "done"
    FAILED = "failed"

    def __str__(self) -> str:
        """Convert enum value to string."""
        return self.value


class FunctionResult(BaseModel):
    """Represents the result of a function execution.

    Attributes:
        action_id: Unique identifier for the action
        action_status: Status of the function execution
        feedback_message: Human-readable message about the execution
        info: Additional information about the execution
    """
    action_id: str
    action_status: FunctionResultStatus
    feedback_message: str
    info: Dict[str, Any]


class Function(BaseModel):
    """Defines a function that can be executed by a worker.

    Attributes:
        fn_name: Name of the function
        fn_description: Description of what the function does
        args: List of arguments the function accepts
        executable: Optional callable that implements the function
    """
    fn_name: str
    fn_description: str
    args: List[Argument]
    executable: Optional[Callable] = None

    def execute(self, fn_id: str, args: Dict[str, Any]) -> FunctionResult:
        """Execute the function using provided arguments.

        Args:
            fn_id: Unique identifier for this function execution
            args: Dictionary of argument names to values

        Returns:
            FunctionResult containing execution status and output
        """
        if not self.executable:
            return FunctionResult(
                action_id=fn_id,
                action_status=FunctionResultStatus.FAILED,
                feedback_message="No executable defined for function",
                info={}
            )

        try:
            status, msg, info = self.executable(**args)
            return FunctionResult(
                action_id=fn_id,
                action_status=status,
                feedback_message=msg,
                info=info
            )
        except Exception as e:
            return FunctionResult(
                action_id=fn_id,
                action_status=FunctionResultStatus.FAILED,
                feedback_message=f"Error executing function: {str(e)}",
                info={}
            )


class ActionType(str, Enum):
    """Type of action returned by the GAME API.

    Attributes:
        CALL_FUNCTION: Execute a function
        CONTINUE_FUNCTION: Continue executing a function
        WAIT: Wait for a condition
        GO_TO: Navigate to a different state
    """
    CALL_FUNCTION = "call_function"
    CONTINUE_FUNCTION = "continue_function"
    WAIT = "wait"
    GO_TO = "go_to"


class HLPResponse(BaseModel):
    """High-level planning response from the GAME API.

    Attributes:
        plan_id: Unique identifier for the plan
        observation_reflection: Reflection on current observations
        plan: List of planned steps
        plan_reasoning: Reasoning behind the plan
        current_state_of_execution: Current execution state
        change_indicator: Indicator of plan changes
        log: Log of events
    """
    plan_id: str
    observation_reflection: str
    plan: List[str]
    plan_reasoning: str
    current_state_of_execution: str
    change_indicator: Optional[str] = None
    log: Optional[List[Dict[str, Any]]] = None


class LLPResponse(BaseModel):
    """Low-level planning response from the GAME API.

    Attributes:
        plan_id: Unique identifier for the plan
        plan_reasoning: Reasoning behind the plan
        situation_analysis: Analysis of the current situation
        plan: List of planned steps
        change_indicator: Indicator of plan changes
        reflection: Reflection on the plan
    """
    plan_id: str
    plan_reasoning: str
    situation_analysis: str
    plan: List[str]
    change_indicator: Optional[str] = None
    reflection: Optional[str] = None


class CurrentTaskResponse(BaseModel):
    """Response containing information about the current task.

    Attributes:
        task: Description of the current task
        task_reasoning: Reasoning behind the task
        location_id: Identifier for the task location
        llp: Low-level planning response
    """
    task: str
    task_reasoning: str
    location_id: Optional[str] = None
    llp: Optional[LLPResponse] = None


class AgentStateResponse(BaseModel):
    """Response containing the current state of an agent.

    Attributes:
        hlp: High-level planning state
        current_task: Current task state
    """
    hlp: Optional[HLPResponse] = None
    current_task: Optional[CurrentTaskResponse] = None


class ActionResponse(BaseModel):
    """Response containing an action to be taken.

    Attributes:
        action_type: Type of action to take
        agent_state: Current state of the agent
        action_args: Arguments for the action
    """
    action_type: ActionType
    agent_state: AgentStateResponse
    action_args: Dict[str, Any]
