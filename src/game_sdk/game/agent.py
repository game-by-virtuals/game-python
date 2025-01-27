"""
Agent module for the GAME SDK.

This module provides the core Agent and supporting classes for creating and managing
GAME agents. It handles agent state management, worker coordination, and session tracking.

Key Components:
- Session: Manages agent session state
- Agent: Main agent class that coordinates workers and handles state

Example:
    # Create a simple agent
    agent = Agent(
        api_key="your_api_key",
        name="My Agent",
        agent_description="A helpful agent",
        agent_goal="To assist users",
        get_agent_state_fn=lambda x, y: {"status": "ready"}
    )
"""

from typing import List, Optional, Callable, Dict, Any
import uuid
from game_sdk.game.worker import Worker
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import Function, FunctionResult, FunctionResultStatus, ActionResponse, ActionType
from game_sdk.game.utils import create_agent, create_workers, post
from game_sdk.game.exceptions import ValidationError


class Session:
    """Manages agent session state.

    A Session represents a single interaction context with an agent.
    It maintains session-specific data like IDs and function results.

    Attributes:
        id (str): Unique session identifier
        function_result (Optional[FunctionResult]): Result of the last executed function

    Example:
        session = Session()
        print(f"Session ID: {session.id}")
    """

    def __init__(self):
        """Initialize a new session with a unique ID."""
        self.id = str(uuid.uuid4())
        self.function_result: Optional[FunctionResult] = None

    def reset(self):
        """Reset the session state.

        Creates a new session ID and clears any existing function results.
        """
        self.id = str(uuid.uuid4())
        self.function_result = None


class Agent:
    """Main agent class for the GAME SDK.

    The Agent class coordinates workers and manages the overall agent state.
    It handles agent creation, worker management, and state transitions.

    Attributes:
        name (str): Agent name
        agent_goal (str): Primary goal of the agent
        agent_description (str): Description of agent capabilities
        workers (Dict[str, WorkerConfig]): Configured workers
        agent_state (dict): Current agent state
        agent_id (str): Unique identifier for the agent

    Args:
        api_key (str): API key for authentication
        name (str): Agent name
        agent_goal (str): Primary goal of the agent
        agent_description (str): Description of agent capabilities
        get_agent_state_fn (Callable): Function to get agent state
        workers (Optional[List[WorkerConfig]]): List of worker configurations

    Raises:
        ValueError: If API key is not set
        ValidationError: If state function returns invalid data
        APIError: If agent creation fails
        AuthenticationError: If API key is invalid

    Example:
        agent = Agent(
            api_key="your_api_key",
            name="Support Agent",
            agent_goal="Help users with issues",
            agent_description="A helpful support agent",
            get_agent_state_fn=get_state
        )
    """

    def __init__(
        self,
        api_key: str,
        name: str,
        agent_goal: str,
        agent_description: str,
        get_agent_state_fn: Callable,
        workers: Optional[List[WorkerConfig]] = None,
    ):
        self._base_url: str = "https://api.virtuals.io"
        self._api_key: str = api_key

        # Validate API key
        if not self._api_key:
            raise ValueError("API key not set")

        # Initialize session
        self._session = Session()

        # Set basic agent properties
        self.name = name
        self.agent_goal = agent_goal
        self.agent_description = agent_description

        # Set up workers
        if workers is not None:
            self.workers = {w.id: w for w in workers}
        else:
            self.workers = {}
        self.current_worker_id = None

        # Set up agent state function
        self.get_agent_state_fn = get_agent_state_fn

        # Validate state function
        initial_state = self.get_agent_state_fn(None, None)
        if not isinstance(initial_state, dict):
            raise ValidationError("State function must return a dictionary")

        # Initialize agent state
        self.agent_state = initial_state

        # Create agent instance
        self.agent_id = create_agent(
            self._base_url,
            self._api_key,
            self.name,
            self.agent_description,
            self.agent_goal
        )

    def compile(self):
        """Compile the agent by setting up its workers.

        This method initializes all workers and creates the necessary
        task generator configurations.

        Raises:
            ValueError: If no workers are configured
            ValidationError: If worker state functions return invalid data
            APIError: If worker creation fails

        Example:
            agent.compile()
        """
        if not self.workers:
            raise ValueError("No workers configured")

        # Create worker instances
        create_workers(
            self._base_url,
            self._api_key,
            list(self.workers.values())
        )

    def reset(self):
        """Reset the agent session.

        Creates a new session ID and clears any existing function results.
        """
        self._session.reset()

    def add_worker(self, worker_config: WorkerConfig):
        """Add a worker to the agent's worker dictionary.

        Args:
            worker_config (WorkerConfig): Worker configuration to add

        Returns:
            Dict[str, WorkerConfig]: Updated worker dictionary
        """
        self.workers[worker_config.id] = worker_config
        return self.workers

    def get_worker_config(self, worker_id: str):
        """Get a worker configuration from the agent's worker dictionary.

        Args:
            worker_id (str): ID of the worker to retrieve

        Returns:
            WorkerConfig: Worker configuration for the given ID
        """
        return self.workers[worker_id]

    def get_worker(self, worker_id: str):
        """Get a worker instance from the agent's worker dictionary.

        Args:
            worker_id (str): ID of the worker to retrieve

        Returns:
            Worker: Worker instance for the given ID
        """
        worker_config = self.get_worker_config(worker_id)
        return Worker(worker_config)

    def _get_action(
        self,
        function_result: Optional[FunctionResult] = None
    ):
        """Get the next action from the GAME API.

        Args:
            function_result (Optional[FunctionResult]): Result of the last executed function

        Returns:
            ActionResponse: Next action from the GAME API
        """
        # Update agent state
        self.agent_state = self.get_agent_state_fn(function_result, self.agent_state)

        # Get next action from API
        response = post(
            self._base_url,
            self._api_key,
            endpoint="/v2/actions",
            data={
                "agent_id": self.agent_id,
                "session_id": self._session.id,
                "state": self.agent_state,
                "function_result": function_result.to_dict() if function_result else None
            }
        )

        return ActionResponse(response)

    def step(self):
        """Take a step in the agent's workflow.

        This method gets the next action from the GAME API, executes it,
        and updates the agent's state.
        """
        # Get next action
        action = self._get_action(self._session.function_result)

        # Execute action
        if action.action_type == ActionType.FUNCTION:
            # Get worker for function execution
            if action.worker_id:
                worker = self.get_worker(action.worker_id)
                if not worker:
                    raise ValueError(f"Worker {action.worker_id} not found")

                # Execute function
                function_result = worker.execute_function(
                    action.function_name,
                    action.function_args
                )

                # Update session with function result
                self._session.function_result = function_result

    def run(self):
        """Run the agent's workflow.

        This method starts the agent's workflow and continues until stopped.
        """
        while True:
            self.step()
