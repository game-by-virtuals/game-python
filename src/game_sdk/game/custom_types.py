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
        print(f"Function Args: {args}")
        print(f"Function ID: {fn_id}")
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

    def __str__(self) -> str:
        steps = ""
        for index, step in enumerate(self.plan):
            steps += f"#{index+1} {str(step)} \n"

        logs_str = ""
        for index, log_item in enumerate(self.log):
            logs_str += f"#{index+1} {str(log_item)} \n"

        output = (
            f"🟢 HLP Response:\n"
            f"- Plan ID: {self.plan_id}\n"
            f"- Reflection on Observation:\n{self.observation_reflection}\n"
            # f"- Steps in Plan:\n{steps}\n"
            f"- Plan Reasoning:\n{self.plan_reasoning}\n"
            # f"- Current State in Plan:\n{self.current_state_of_execution}\n"
            # f"- Change Indicator: {self.change_indicator}\n"
            # f"- Logs:\n{logs_str}\n"
        )
        return output


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

    def __str__(self) -> str:
        steps = ""
        for index, step in enumerate(self.plan):
            steps += f"#{index+1} {str(step)} \n"

        output = (
            f"🟢 LLP Response:\n"
            f"- Plan ID: {self.plan_id}\n"
            f"- Plan Reasoning:\n{self.plan_reasoning}\n"
            f"- Situation Analysis:\n{self.situation_analysis}\n"
            f"- Steps in Plan:\n{steps}\n"
            f"- Change Indicator: {self.change_indicator}\n"
            f"- Reflections on Plan:\n{self.reflection}\n"
        )
        return output


@dataclass(frozen=True)
class ReasoningAction:
    """
    Represents a detailed reasoning step for a specific task action, including reflections,
    reasoning for the current task, the rationale for the next step, and the function to execute.

    Attributes:
        id (str): Unique identifier for this reasoning action or step.
        task_reflection (str): Reflection on the outcomes or status of the current or previous task.
        task_reasoning (str): Explanation of the reasoning behind the current task or decision.
        next_step_reaseaning (str): Justification for the next step or action to be taken.
        fn_name (str): Name of the function that should be called to perform the next step.
    """
    id: str
    task_reflection: str
    task_reasoning: str
    next_step_reasoning: str
    fn_name: str

    def __str__(self) -> str:
        output = (
            f"Reasoning Action {self.id}\n"
            f"- Task Reflection: {self.task_reflection}\n"
            f"- Task Reasoning: {self.task_reasoning}\n"
            f"- Next Step Reasoning: {self.next_step_reasoning}\n"
            f"- Function Name: {self.fn_name}\n"
        )
        return output

@dataclass(frozen=True)
class RecentReasoningResponse:
    """
    Represents the most recent reasoning response from the GAME API, detailing the current task,
    the reasoning behind the plan, reflections on previous plans, and the next steps to take.

    Attributes:
        id (str): Unique identifier for the reasoning response or task.
        plan_reflection (str): Reflection on the progress and context of the current plan.
        plan_reasoning (str): Explanation of the rationale behind the current plan.
        next_task_reasoning (str): Justification for the next task to be performed.
        task (str): Description of the current task to be executed.
        worker_id (str): Identifier of the worker or agent responsible for executing the task.
        actions (List[str]): List of actions to be taken as part of the current task.
    """
    id: str
    plan_reflection: str
    plan_reasoning: str
    next_task_reasoning: str
    task: str
    worker_id: str
    actions: List[ReasoningAction]

    def __str__(self) -> str:
        curr_actions = ""
        for index, action in enumerate(self.actions):
            curr_actions += f"#{index+1} {str(action)} \n"

        output = (
            f"Recent Reasoning\n"
            f"- {self.id}: {self.task}\n"
            f"- Plan Reflection:\n{self.plan_reflection}\n"
            f"- Plan Reasoning:\n{self.plan_reasoning}\n"
            f"- Worker ID: {self.worker_id}\n"
            # f"- Actions to take:\n{curr_actions}\n"
        )
        return output
    

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
    task_id: str
    task: str
    task_reasoning: str
    task_result: Optional[str]
    location_id: str = field(default="*not provided*")
    llp: Optional[LLPResponse] = None

    def __str__(self) -> str:
        llp_response = "- LLP Response: None\n" if not self.llp else self.llp

        output = (
            f"⏳ Current Task: {self.task}\n"
            f"- Task ID: {self.task_id}\n"
            f"- Task Reason:\n{self.task_reasoning}\n"
            f"- Task Result:\n{self.task_result}\n"
            f"- Location ID: {self.location_id}\n"
            # f"{llp_response}\n"
        )
        return output


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
    recent_reasoning: Optional[List[RecentReasoningResponse]] = None

    def __str__(self) -> str:
        recent_reasonings = ""
        if self.recent_reasoning:
            for index, reason in enumerate(self.recent_reasoning):
                recent_reasonings += f"💭 #{index+1} {str(reason)}\n"

        output = (
            f"{self.hlp}"
            f"{self.current_task}"
            f"{recent_reasonings}"
        )
        return output

# ActionResponse format returned from GAME API call
class ActionResponse(BaseModel):
    """
    Represents the response format from the GAME API when selecting an Action.

    Attributes:
        action_type (ActionType): Type of action.
        agent_state (AgentStateResponse): Agent state response.
        action_args (Optional[Dict[str, Any]]): Additional action arguments.
        reaction_info (Optional[str]): TODO: Get explanation from Steven Lee
        agents (Optional[List[str]]): TODO: Get explanation from Steven Lee
    """
    action_type: ActionType
    agent_state: AgentStateResponse
    action_args: Optional[Dict[str, Any]] = None
    reaction_info: Optional[str] = None
    agents: Optional[List[str]] = None

    def __str__(self) -> str:
        output = (
            f"========= 📋 Action Response =========\n"
            f"# Action Type: {self.action_type.value}\n\n"
            f"# Agent State:\n{self.agent_state}\n\n"
            f"# Action Arguments:\n{self.action_args}\n\n"
            f"# Reaction Info:\n{self.reaction_info}\n\n"
            # f"# Agents:\n{self.agents}\n\n"
            f"========= Action Response End ========\n"
        )
        return output


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
