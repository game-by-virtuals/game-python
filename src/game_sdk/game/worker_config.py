"""
Worker Configuration Module for the GAME SDK.

This module provides the WorkerConfig class which is responsible for configuring
worker behavior, action space, and state management. It serves as a configuration
container that defines how a worker should behave and what actions it can perform.

Example:
    >>> from game_sdk.game.worker_config import WorkerConfig
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
    ...     action_space=[search_fn],
    ...     instruction="Search efficiently"
    ... )
"""

from typing import List, Optional, Callable, Dict
from game_sdk.game.custom_types import Function

class WorkerConfig:
    """Configuration for a worker instance.

    The WorkerConfig class defines how a worker behaves, including its action space,
    state management, and description. It serves as a blueprint for creating worker
    instances and ensures consistent worker behavior.

    Attributes:
        id (str): Unique identifier for the worker
        worker_description (str): Description of the worker's capabilities
        instruction (str): Specific instructions for the worker
        get_state_fn (Callable): Function to get worker's current state
        action_space (Dict[str, Function]): Available actions for the worker
        api_key (str, optional): API key for worker authentication

    Args:
        id (str): Worker identifier
        worker_description (str): Description of worker capabilities
        get_state_fn (Callable): State retrieval function that takes function_result
            and current_state as arguments and returns a dict
        action_space (List[Function]): List of available actions as Function objects
        instruction (str, optional): Additional instructions for the worker
        api_key (str, optional): API key for worker authentication

    Example:
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
        ...     action_space=[search_fn],
        ...     instruction="Search efficiently"
        ... )
    """

    def __init__(
        self,
        id: str,
        worker_description: str,
        get_state_fn: Callable,
        action_space: List[Function],
        instruction: Optional[str] = "",
        api_key: Optional[str] = None,
    ):
        """Initialize a new WorkerConfig instance.

        Args:
            id (str): Worker identifier
            worker_description (str): Description of worker capabilities
            get_state_fn (Callable): State retrieval function
            action_space (List[Function]): List of available actions
            instruction (str, optional): Additional instructions for the worker
            api_key (str, optional): API key for worker authentication

        Note:
            The get_state_fn will be wrapped to include instructions in the state.
            The action_space list will be converted to a dictionary for easier lookup.
        """
        self.id = id
        self.worker_description = worker_description
        self.instruction = instruction
        self.get_state_fn = get_state_fn
        self.api_key = api_key
        
        # Setup get state function with instructions
        self.get_state_fn = lambda function_result, current_state: {
            "instructions": self.instruction,
            **get_state_fn(function_result, current_state),
        }

        # Convert action space list to dictionary for easier lookup
        self.action_space: Dict[str, Function] = {
            f.get_function_def()["fn_name"]: f for f in action_space
        }
