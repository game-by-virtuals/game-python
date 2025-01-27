"""Worker module for the GAME SDK.

Provides the Worker class that executes functions and manages state.
"""

from typing import Dict, Any
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import FunctionResult, FunctionResultStatus


class Worker:
    """
    A worker that can execute functions and manage state.

    Attributes:
        config: Configuration for the worker
        state: Current state of the worker
    """

    def __init__(self, config: WorkerConfig):
        """
        Initialize a new Worker instance.

        Args:
            config: Configuration defining worker behavior
        """
        self.config = config
        self.state = config.state or {}

    def execute_function(
        self,
        fn_name: str,
        fn_id: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a function and update worker state.

        Args:
            fn_name: Name of function to execute
            fn_id: Unique identifier for this execution
            args: Arguments to pass to the function

        Returns:
            Dict containing execution result and updated state
        """
        # Get function from config
        fn = next(
            (f for f in self.config.functions if f.fn_name == fn_name),
            None
        )
        if not fn:
            return {
                "result": FunctionResult(
                    action_id=fn_id,
                    action_status=FunctionResultStatus.FAILED,
                    feedback_message=f"Function {fn_name} not found",
                    info={}
                ),
                "state": self.state
            }

        # Execute function
        result = fn.execute(fn_id=fn_id, args=args)

        # Update state
        self.state = self._update_state(result)

        return {
            "result": result,
            "state": self.state
        }

    def _update_state(self, result: FunctionResult) -> Dict[str, Any]:
        """
        Update worker state based on function result.

        Args:
            result: Result from function execution

        Returns:
            Updated state dictionary
        """
        return {
            **self.state,
            "last_result": result.model_dump()
        }
