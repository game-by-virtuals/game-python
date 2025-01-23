"""Worker module for handling autonomous task execution."""
from typing import Any, Callable, Dict, Optional, List
from game_sdk.game.custom_types import Function, FunctionResult, FunctionResultStatus, ActionResponse, ActionType
from game_sdk.game.utils import create_agent, post

class Worker:
    """
    An interactable worker agent that can autonomously complete tasks with its available functions.
    
    This class provides functionality to create and manage a worker that can:
    - Execute tasks autonomously
    - Maintain state between actions
    - Handle function results and state updates
    
    Attributes:
        description (str): Description of the worker/character card (PROMPT)
        instruction (str): Specific additional instruction for the worker (PROMPT)
        get_state_fn (Callable): Function to get the current state
        state (Dict): Current state of the worker
        action_space (Dict[str, Function]): Available functions/tools for the worker
    """

    def __init__(
        self,
        api_key: str,
        description: str,
        get_state_fn: Callable,
        action_space: List[Function],
        instruction: str = "",
    ):
        """
        Initialize a Worker instance.
        
        Args:
            api_key (str): API key for authentication
            description (str): Description of the worker/character card
            get_state_fn (Callable): Function to get the current state
            action_space (List[Function]): List of available functions
            instruction (str, optional): Additional instructions for the worker. Defaults to "".
            
        Raises:
            ValueError: If api_key is not set
        """
        self._base_url: str = "https://game.virtuals.io"
        self._api_key: str = api_key

        if not self._api_key:
            raise ValueError("API key not set")

        self.description: str = description
        self.instruction: str = instruction
        self._get_state_fn = get_state_fn

        # Setup get state function and initial state
        self.get_state_fn = lambda function_result, current_state: {
            "instructions": self.instruction,
            **self._get_state_fn(function_result, current_state),
        }

        # Initialize with dummy function result
        dummy_function_result = FunctionResult(
            action_id="",
            action_status=FunctionResultStatus.DONE,
            feedback_message="",
            info={},
        )
        self.state = self.get_state_fn(dummy_function_result, None)

        # Setup action space
        self.action_space = {
            f.get_function_def()["fn_name"]: f for f in action_space
        } if not isinstance(action_space, dict) else action_space

        # Initialize agent
        self._agent_id: str = create_agent(
            api_key=self._api_key,
            description=self.description,
            instruction=self.instruction
        )

        # Persistent variables
        self._submission_id: Optional[str] = None
        self._function_result: Optional[FunctionResult] = None

    def set_task(self, task: str) -> str:
        """
        Set a task for the worker to execute.
        
        Args:
            task (str): The task description
            
        Returns:
            str: The submission ID for the task
            
        Raises:
            ValueError: If the task cannot be assigned
        """
        response = post(
            base_url=self._base_url,
            api_key=self._api_key,
            endpoint=f"/v2/agents/{self._agent_id}/tasks",
            data={"task": task},
        )

        self._submission_id = response.get("submission_id")
        if not self._submission_id:
            raise ValueError(f"Failed to assign task: {response}")

        return self._submission_id

    def _get_action(self, function_result: Optional[FunctionResult] = None) -> ActionResponse:
        """
        Get the next action from the GAME API.
        
        Args:
            function_result (Optional[FunctionResult]): Results of the previous action
            
        Returns:
            ActionResponse: The next action to execute
        """
        if function_result is None:
            function_result = FunctionResult(
                action_id="",
                action_status=FunctionResultStatus.DONE,
                feedback_message="",
                info={},
            )

        data = {
            "environment": self.state,
            "functions": [f.get_function_def() for f in self.action_space.values()],
            "action_result": function_result.model_dump(exclude={'info'}) if function_result else None,
        }

        response = post(
            base_url=self._base_url,
            api_key=self._api_key,
            endpoint=f"/v2/agents/{self._agent_id}/tasks/{self._submission_id}/next",
            data=data,
        )

        return ActionResponse.model_validate(response)

    def step(self) -> tuple[ActionResponse, Optional[FunctionResult]]:
        """
        Execute the next step in the current task.
        
        Returns:
            tuple[ActionResponse, Optional[FunctionResult]]: The action response and function result
            
        Raises:
            ValueError: If no task is set or if there's an unexpected action type
        """
        if not self._submission_id:
            raise ValueError("No task set")

        action_response = self._get_action(self._function_result)
        action_type = action_response.action_type

        if action_type == ActionType.CALL_FUNCTION:
            if not action_response.action_args:
                raise ValueError("No function information provided by GAME")

            self._function_result = self.action_space[
                action_response.action_args["fn_name"]
            ].execute(**action_response.action_args)

            self.state = self.get_state_fn(self._function_result, self.state)

        elif action_type == ActionType.WAIT:
            self._submission_id = None
            self._function_result = None

        else:
            raise ValueError(f"Unexpected action type: {action_type}")

        return action_response, self._function_result.model_copy() if self._function_result else None

    def run(self, task: str) -> None:
        """
        Execute a task autonomously until completion.
        
        Args:
            task (str): The task to execute
        """
        self.set_task(task)
        while self._submission_id:
            self.step()
