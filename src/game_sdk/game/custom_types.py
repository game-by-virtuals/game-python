from typing import Any, Dict, Optional, List, Union, Sequence, Callable, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class Argument(BaseModel):
    """
    Represents an argument definition for a GAME SDK function.

    Attributes:
        name (str): The name of the argument.
        description (str): A clear description of what the argument does.
        type (Optional[Union[List[str], str]]): The expected type(s) of the argument.
        optional (Optional[bool]): Whether this argument is optional, defaults to False.
    """
    name: str
    description: str
    type: Optional[Union[List[str], str]] = None
    optional: Optional[bool] = False

class FunctionResultStatus(str, Enum):
    """
    Enum representing the possible status outcomes of a function execution.

    Values:
        DONE: Function completed successfully
        FAILED: Function execution failed
    """
    DONE = "done"
    FAILED = "failed"

class FunctionResult(BaseModel):
    """
    Represents the result of executing a GAME SDK function.

    Attributes:
        action_id (str): Unique identifier for the action.
        action_status (FunctionResultStatus): Status of the function execution (DONE/FAILED).
        feedback_message (Optional[str]): Human-readable message about the execution result.
        info (Optional[Dict[str, Any]]): Additional information or data from the execution.
    """
    action_id: str
    action_status: FunctionResultStatus
    feedback_message: Optional[str] = None
    info: Optional[Dict[str, Any]] = None

class Function(BaseModel):
    """
    Defines a callable function within the GAME SDK.

    This class represents a function that can be executed by the GAME system. It includes
    metadata about the function as well as the actual executable implementation.

    Attributes:
        fn_name (str): Name of the function.
        fn_description (str): Detailed description of what the function does.
        args (List[Argument]): List of arguments the function accepts.
        hint (Optional[str]): Optional usage hint or example.
        executable (Callable): The actual function implementation to be called.
    """
    fn_name: str
    fn_description: str
    args: List[Argument]
    hint: Optional[str] = None
    
    # Make executable required but with a default value
    executable: Callable[..., Tuple[FunctionResultStatus, str, dict]] = Field(
        default_factory=lambda: Function._default_executable
    )

    def get_function_def(self):
        """
        Returns the function definition without the executable component.

        Returns:
            dict: Function metadata excluding the executable field.
        """
        return self.model_dump(exclude={'executable'})

    @staticmethod
    def _default_executable(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """
        Default no-op implementation for functions.

        Returns:
            Tuple[FunctionResultStatus, str, dict]: Returns DONE status with a default message.
        """
        return FunctionResultStatus.DONE, "Default implementation - no action taken", {}
    
    def execute(self, **kwds: Any) -> FunctionResult:
        """
        Executes the function with the provided arguments.

        Args:
            **kwds: Keyword arguments including:
                - fn_id: Function identifier
                - args: Dictionary of argument names and values

        Returns:
            FunctionResult: Result of the function execution including status and feedback.

        Raises:
            Any exceptions from the executable are caught and returned as a FAILED FunctionResult.
        """
        fn_id = kwds.get('fn_id')
        args = kwds.get('args', {})

        try:
            # Extract values from the nested dictionary structure
            processed_args = {}
            for arg_name, arg_value in args.items():
                if isinstance(arg_value, dict) and 'value' in arg_value:
                    processed_args[arg_name] = arg_value['value']
                else:
                    processed_args[arg_name] = arg_value
                    
            # print("Processed args: ", processed_args)
            # execute the function provided
            status, feedback, info = self.executable(**processed_args)

            return FunctionResult(
                action_id=fn_id,
                action_status=status,
                feedback_message=feedback,
                info=info,
            )
        except Exception as e:
            return FunctionResult(
                action_id=fn_id,
                action_status=FunctionResultStatus.FAILED,
                feedback_message=f"Error executing function: {str(e)}",
                info={},
            )

# Different ActionTypes returned by the GAME API
class ActionType(Enum):
    """
    Defines the types of actions that can be returned by the GAME API.

    Values:
        CALL_FUNCTION: Execute a function call
        CONTINUE_FUNCTION: Continue a previous function execution
        WAIT: Wait for a specified duration
        GO_TO: Navigate to a specified location
    """
    CALL_FUNCTION = "call_function"
    CONTINUE_FUNCTION = "continue_function"
    WAIT = "wait"
    GO_TO = "go_to"


## set of different data structures required by the ActionResponse returned from GAME ##
@dataclass(frozen=True)
class HLPResponse:
    """
    Represents a High-Level Plan (HLP) response from the GAME API.

    Attributes:
        plan_id (str): Unique identifier for the plan.
        observation_reflection (str): Reflection on the current observation.
        plan (Sequence[str]): List of steps in the plan.
        plan_reasoning (str): Reasoning behind the plan.
        current_state_of_execution (str): Current state of the plan execution.
        change_indicator (Optional[str]): Indicator of changes in the plan.
        log (Sequence[dict]): Log of plan execution.
    """
    plan_id: str
    observation_reflection: str
    plan: Sequence[str]
    plan_reasoning: str
    current_state_of_execution: str
    change_indicator: Optional[str] = None
    log: Sequence[dict] = field(default_factory=list)


@dataclass(frozen=True)
class LLPResponse:
    """
    Represents a Low-Level Plan (LLP) response from the GAME API.

    Attributes:
        plan_id (str): Unique identifier for the plan.
        plan_reasoning (str): Reasoning behind the plan.
        situation_analysis (str): Analysis of the current situation.
        plan (Sequence[str]): List of steps in the plan.
        change_indicator (Optional[str]): Indicator of changes in the plan.
        reflection (Optional[str]): Reflection on the plan execution.
    """
    plan_id: str
    plan_reasoning: str
    situation_analysis: str
    plan: Sequence[str]
    change_indicator: Optional[str] = None
    reflection: Optional[str] = None


@dataclass(frozen=True)
class CurrentTaskResponse:
    """
    Represents the current task response from the GAME API.

    Attributes:
        task (str): Current task.
        task_reasoning (str): Reasoning behind the task.
        location_id (str): Location identifier (defaults to "*not provided*").
        llp (Optional[LLPResponse]): Low-Level Plan response.
    """
    task: str
    task_reasoning: str
    location_id: str = field(default="*not provided*")
    llp: Optional[LLPResponse] = None


@dataclass(frozen=True)
class AgentStateResponse:
    """
    Represents the agent state response from the GAME API.

    Attributes:
        hlp (Optional[HLPResponse]): High-Level Plan response.
        current_task (Optional[CurrentTaskResponse]): Current task response.
    """
    hlp: Optional[HLPResponse] = None
    current_task: Optional[CurrentTaskResponse] = None

# ActionResponse format returned from GAME API call
class ActionResponse(BaseModel):
    """
    Represents the response format from the GAME API when selecting an Action.

    Attributes:
        action_type (ActionType): Type of action.
        agent_state (AgentStateResponse): Agent state response.
        action_args (Optional[Dict[str, Any]]): Additional action arguments.
    """
    action_type: ActionType
    agent_state: AgentStateResponse
    action_args: Optional[Dict[str, Any]] = None


class ChatActionRequest(BaseModel):
    fn_name: str
    args: Dict[str, Any]
    id: str

class GameChatResponse(BaseModel):
    message: Optional[str] = Field(default=None)
    is_finished: bool = Field(default=False)
    function_call: Optional[ChatActionRequest] = Field(default=None)

class AgentMessage(BaseModel):
    message: str
    chat_id: str

class FunctionCallResponse(BaseModel):
    fn_name: str
    fn_args: Dict[str, Any]
    result: FunctionResult

class ChatResponse(BaseModel):
    message: str
    is_finished: bool
    function_call: Optional[FunctionCallResponse] = None
