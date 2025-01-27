"""
Custom types and data structures for the GAME SDK.

This module defines the core data structures and types used throughout the GAME SDK,
including function definitions, arguments, results, and API responses.

Example:
    >>> from game_sdk.game.custom_types import Function, Argument
    >>> 
    >>> # Create a function definition
    >>> weather_fn = Function(
    ...     fn_name="get_weather",
    ...     fn_description="Get weather for a city",
    ...     args=[
    ...         Argument(
    ...             name="city",
    ...             description="City name",
    ...             type="string"
    ...         )
    ...     ]
    ... )
    >>> 
    >>> # Execute the function
    >>> result = weather_fn.execute(fn_id="123", args={"city": {"value": "New York"}})
    >>> print(result.action_status)
    'done'
"""

from typing import Any, Dict, Optional, List, Union, Sequence, Callable, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Argument(BaseModel):
    """
    Defines an argument for a function in the GAME SDK.
    
    Attributes:
        name (str): Name of the argument
        description (str): Description of the argument's purpose
        type (Optional[Union[List[str], str]]): Type(s) of the argument (e.g., "string", "integer")
        optional (Optional[bool]): Whether the argument is optional
        
    Example:
        >>> city_arg = Argument(
        ...     name="city",
        ...     description="City to get weather for",
        ...     type="string",
        ...     optional=False
        ... )
    """
    name: str
    description: str
    type: Optional[Union[List[str], str]] = None
    optional: Optional[bool] = False


class FunctionResultStatus(str, Enum):
    """
    Status of a function execution.
    
    Attributes:
        DONE: Function completed successfully
        FAILED: Function failed to complete
        
    Example:
        >>> status = FunctionResultStatus.DONE
        >>> print(status)
        'done'
        >>> str(status)
        'done'
    """
    DONE = "done"
    FAILED = "failed"
    
    def __str__(self) -> str:
        """Convert enum value to string."""
        return self.value


class FunctionResult(BaseModel):
    """
    Result of a function execution.
    
    Attributes:
        action_id (str): Unique identifier for the action
        action_status (FunctionResultStatus): Status of the action
        feedback_message (Optional[str]): Human-readable feedback
        info (Optional[Dict[str, Any]]): Additional information
        
    Example:
        >>> result = FunctionResult(
        ...     action_id="123",
        ...     action_status=FunctionResultStatus.DONE,
        ...     feedback_message="Weather fetched successfully",
        ...     info={"temperature": "20°C"}
        ... )
    """
    action_id: str
    action_status: FunctionResultStatus
    feedback_message: Optional[str] = None
    info: Optional[Dict[str, Any]] = None


class Function(BaseModel):
    """
    Defines a function that can be executed by a worker.
    
    Attributes:
        fn_name (str): Name of the function
        fn_description (str): Description of what the function does
        args (List[Argument]): List of function arguments
        hint (Optional[str]): Optional usage hint
        executable (Callable): Function to execute
        
    Example:
        >>> def get_weather(city: str) -> Tuple[FunctionResultStatus, str, dict]:
        ...     return FunctionResultStatus.DONE, "Success", {"temp": "20°C"}
        >>> 
        >>> weather_fn = Function(
        ...     fn_name="get_weather",
        ...     fn_description="Get weather for a city",
        ...     args=[
        ...         Argument(
        ...             name="city",
        ...             description="City name",
        ...             type="string"
        ...         )
        ...     ],
        ...     executable=get_weather
        ... )
    """
    fn_name: str
    fn_description: str
    args: List[Argument]
    hint: Optional[str] = None
    
    # Make executable required but with a default value
    executable: Callable[..., Tuple[FunctionResultStatus, str, dict]] = Field(
        default_factory=lambda: Function._default_executable
    )

    def get_function_def(self) -> Dict[str, Any]:
        """
        Get the function definition without the executable.
        
        Returns:
            Dict containing function metadata (excluding executable)
        """
        return self.model_dump(exclude={'executable'})

    @staticmethod
    def _default_executable(**kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        """
        Default executable that does nothing.
        
        Returns:
            Tuple of (status, message, info)
        """
        return FunctionResultStatus.DONE, "Default implementation - no action taken", {}
    
    def execute(self, **kwds: Any) -> FunctionResult:
        """
        Execute the function using arguments from GAME action.
        
        Args:
            **kwds: Keyword arguments including:
                - fn_id: Function ID
                - args: Function arguments
                
        Returns:
            FunctionResult containing execution status and results
            
        Example:
            >>> result = weather_fn.execute(
            ...     fn_id="123",
            ...     args={"city": {"value": "New York"}}
            ... )
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
                    
            logger.debug(f"Executing function {self.fn_name} with args: {processed_args}")
            
            # Execute the function provided
            status, feedback, info = self.executable(**processed_args)

            return FunctionResult(
                action_id=fn_id,
                action_status=status,
                feedback_message=feedback,
                info=info,
            )
        except Exception as e:
            logger.error(f"Error executing function {self.fn_name}: {e}")
            return FunctionResult(
                action_id=fn_id,
                action_status=FunctionResultStatus.FAILED,
                feedback_message=f"Error executing function: {str(e)}",
                info={},
            )


class ActionType(str, Enum):
    """
    Types of actions returned by the GAME API.
    
    Attributes:
        CALL_FUNCTION: Execute a function
        CONTINUE_FUNCTION: Continue a long-running function
        WAIT: Wait for a condition
        GO_TO: Navigate to a location
        
    Example:
        >>> action = ActionType.CALL_FUNCTION
        >>> print(action)
        'call_function'
    """
    CALL_FUNCTION = "call_function"
    CONTINUE_FUNCTION = "continue_function"
    WAIT = "wait"
    GO_TO = "go_to"


@dataclass(frozen=True)
class HLPResponse:
    """
    High-Level Planner (HLP) response from GAME API.
    
    Attributes:
        plan_id (str): Unique plan identifier
        observation_reflection (str): Reflection on current state
        plan (Sequence[str]): Sequence of planned steps
        plan_reasoning (str): Reasoning behind the plan
        current_state_of_execution (str): Current execution state
        change_indicator (Optional[str]): Indicates state changes
        log (Sequence[dict]): Execution log
        
    Example:
        >>> hlp = HLPResponse(
        ...     plan_id="123",
        ...     observation_reflection="Weather is sunny",
        ...     plan=["Check temperature", "Get forecast"],
        ...     plan_reasoning="Need to provide weather update",
        ...     current_state_of_execution="Checking temperature"
        ... )
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
    Low-Level Planner (LLP) response from GAME API.
    
    Attributes:
        plan_id (str): Unique plan identifier
        plan_reasoning (str): Reasoning behind the plan
        situation_analysis (str): Analysis of current situation
        plan (Sequence[str]): Sequence of planned steps
        change_indicator (Optional[str]): Indicates state changes
        reflection (Optional[str]): Reflection on execution
        
    Example:
        >>> llp = LLPResponse(
        ...     plan_id="123",
        ...     plan_reasoning="Need temperature data",
        ...     situation_analysis="API available",
        ...     plan=["Call weather API", "Process data"]
        ... )
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
    Current task information from GAME API.
    
    Attributes:
        task (str): Current task description
        task_reasoning (str): Reasoning for current task
        location_id (str): Task location identifier
        llp (Optional[LLPResponse]): Associated LLP response
        
    Example:
        >>> task = CurrentTaskResponse(
        ...     task="Get weather data",
        ...     task_reasoning="Need current conditions",
        ...     location_id="NYC",
        ...     llp=llp_response
        ... )
    """
    task: str
    task_reasoning: str
    location_id: str = field(default="*not provided*")
    llp: Optional[LLPResponse] = None


@dataclass(frozen=True)
class AgentStateResponse:
    """
    Agent state information from GAME API.
    
    Attributes:
        hlp (Optional[HLPResponse]): High-level planner response
        current_task (Optional[CurrentTaskResponse]): Current task info
        
    Example:
        >>> state = AgentStateResponse(
        ...     hlp=hlp_response,
        ...     current_task=task_response
        ... )
    """
    hlp: Optional[HLPResponse] = None
    current_task: Optional[CurrentTaskResponse] = None


class ActionResponse(BaseModel):
    """
    Response format from the GAME API when selecting an Action.
    
    Attributes:
        action_type (ActionType): Type of action to perform
        agent_state (AgentStateResponse): Current agent state
        action_args (Optional[Dict[str, Any]]): Action arguments
        
    Example:
        >>> response = ActionResponse(
        ...     action_type=ActionType.CALL_FUNCTION,
        ...     agent_state=agent_state,
        ...     action_args={"function": "get_weather"}
        ... )
    """
    action_type: ActionType
    agent_state: AgentStateResponse
    action_args: Optional[Dict[str, Any]] = None
