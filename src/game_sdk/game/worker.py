"""
Worker Module for the GAME SDK.

This module provides the Worker class which is responsible for executing functions
and managing worker state. Workers are the building blocks of GAME agents and
handle specific tasks based on their configuration.

Example:
    >>> from game_sdk.game.worker_config import WorkerConfig
    >>> from game_sdk.game.worker import Worker
    >>> from game_sdk.game.custom_types import Function
    >>> 
    >>> def get_state(result, state):
    ...     return {"ready": True}
    >>> 
    >>> search_fn = Function(
    ...     name="search",
    ...     description="Search for information",
    ...     executable=lambda query: {"results": []}
    ... )
    >>> 
    >>> config = WorkerConfig(
    ...     id="search_worker",
    ...     worker_description="Searches for information",
    ...     get_state_fn=get_state,
    ...     action_space=[search_fn]
    ... )
    >>> 
    >>> worker = Worker(config)
    >>> result = worker.execute_function("search", {"query": "python"})
"""

from typing import Any, Callable, Dict, Optional, List
from game_sdk.game.custom_types import Function, FunctionResult, FunctionResultStatus, ActionResponse, ActionType
from game_sdk.game.utils import create_agent, post
from game_sdk.game.worker_config import WorkerConfig

class Worker:
    """A worker agent that can execute functions and manage state.

    The Worker class is responsible for executing functions from its action space
    and maintaining its state. It is initialized from a WorkerConfig object that
    defines its behavior and available actions.

    Attributes:
        config (WorkerConfig): Configuration object defining worker behavior
        description (str): Description of worker capabilities
        instruction (str): Additional instructions for the worker
        get_state_fn (Callable): Function to get worker's current state
        action_space (Dict[str, Function]): Available actions
        state (dict): Current worker state

    Args:
        worker_config (WorkerConfig): Configuration object for the worker

    Example:
        >>> config = WorkerConfig(
        ...     id="search_worker",
        ...     worker_description="Searches for information",
        ...     get_state_fn=lambda r, s: {"ready": True},
        ...     action_space=[search_function]
        ... )
        >>> worker = Worker(config)
        >>> result = worker.execute_function("search", {"query": "python"})
    """

    def __init__(
        self,
        worker_config: WorkerConfig,
    ):
        """Initialize a worker from a WorkerConfig object.

        Args:
            worker_config (WorkerConfig): Configuration object that defines
                worker behavior, action space, and state management.
        """
        self.config = worker_config
        self.description = worker_config.worker_description
        self.instruction = worker_config.instruction
        self.get_state_fn = worker_config.get_state_fn
        self.action_space = worker_config.action_space
        self.state = self.get_state_fn(None, None)

    def execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function in the worker's action space.
        
        This method looks up the requested function in the worker's action space
        and executes it with the provided arguments.
        
        Args:
            function_name (str): Name of the function to execute
            args (Dict[str, Any]): Arguments to pass to the function
            
        Returns:
            Dict[str, Any]: Result of the function execution
            
        Raises:
            ValueError: If the function is not found in the action space
            
        Example:
            >>> result = worker.execute_function("search", {"query": "python"})
            >>> print(result)
            {'results': [...]}
        """
        if function_name not in self.action_space:
            raise ValueError(f"Function {function_name} not found in action space")
            
        function = self.action_space[function_name]
        return function.executable(**args)

    def set_task(self, task: str):
        """Sets a task for the worker to execute.
        
        Note:
            This method is not implemented for standalone workers.
            Use execute_function() directly instead.
        
        Args:
            task (str): Task description
            
        Raises:
            NotImplementedError: Always raised for standalone workers
        """
        raise NotImplementedError("Task setting not implemented for standalone workers")

    def _get_action(
        self,
        function_result: Optional[FunctionResult] = None
    ) -> ActionResponse:
        """Gets the next action for the worker to execute.
        
        Note:
            This method is not implemented for standalone workers.
            Use execute_function() directly instead.
        
        Args:
            function_result (Optional[FunctionResult]): Result of previous function
            
        Raises:
            NotImplementedError: Always raised for standalone workers
        """
        raise NotImplementedError("Action getting not implemented for standalone workers")

    def step(self):
        """Takes a step in the worker's workflow.
        
        Note:
            This method is not implemented for standalone workers.
            Use execute_function() directly instead.
            
        Raises:
            NotImplementedError: Always raised for standalone workers
        """
        raise NotImplementedError("Stepping not implemented for standalone workers")

    def run(self):
        """Runs the worker's workflow.
        
        Note:
            This method is not implemented for standalone workers.
            Use execute_function() directly instead.
            
        Raises:
            NotImplementedError: Always raised for standalone workers
        """
        raise NotImplementedError("Running not implemented for standalone workers")
