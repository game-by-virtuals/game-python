from typing import List, Optional, Callable, Dict
import uuid
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import Function, FunctionResult, FunctionResultStatus, ActionResponse, ActionType
from game_sdk.game.api import GAMEClient
from game_sdk.game.api_v2 import GAMEClientV2

class Session:
    """
    Manages a unique session for agent interactions.

    A Session maintains state for a single interaction sequence, including function results
    and a unique identifier. It can be reset to start a fresh interaction sequence.

    Attributes:
        id (str): Unique identifier for the session, generated using UUID4.
        function_result (Optional[FunctionResult]): Result of the last executed function.
    """
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.function_result: Optional[FunctionResult] = None

    def reset(self):
        """
        Resets the session by generating a new ID and clearing function results.
        This is useful when starting a new interaction sequence.
        """
        self.id = str(uuid.uuid4())
        self.function_result = None


class WorkerConfig:
    """
    Configuration for a GAME SDK worker.

    This class defines the behavior and capabilities of a worker within the GAME system.
    Workers are specialized agents that can perform specific tasks using their defined
    action space and state management functions.

    Args:
        id (str): Unique identifier for the worker.
        worker_description (str): Description of the worker's capabilities for task generation.
        get_state_fn (Callable): Function to retrieve the worker's current state.
        action_space (List[Function]): List of functions the worker can execute.
        instruction (Optional[str]): Additional instructions for the worker.

    Attributes:
        id (str): Worker's unique identifier.
        worker_description (str): Description used by task generator.
        instruction (str): Additional worker instructions.
        get_state_fn (Callable): State retrieval function with instruction context.
        action_space (Dict[str, Function]): Available functions mapped by name.
    """
    def __init__(self,
                 id: str,
                 worker_description: str,
                 get_state_fn: Callable,
                 action_space: List[Function],
                 instruction: Optional[str] = None,
                 ):

        self.id = id  # id or name of the worker
        # worker description for the TASK GENERATOR (to give appropriate tasks) [NOT FOR THE WORKER ITSELF - WORKER WILL STILL USE AGENT DESCRIPTION]
        self.worker_description = worker_description
        self.instruction = instruction
        self.get_state_fn = get_state_fn

        # setup get state function with the instructions
        self.get_state_fn = lambda function_result, current_state: {
            "instructions": self.instruction,  # instructions are set up in the state
            # places the rest of the output of the get_state_fn in the state
            **get_state_fn(function_result, current_state),
        }

        self.action_space: Dict[str, Function] = {
            f.get_function_def()["fn_name"]: f for f in action_space
        }


class Agent:
    """
    Main agent class for the GAME SDK.

    The Agent class represents an autonomous agent that can perform tasks using configured
    workers. It manages the interaction flow, state management, and task execution within
    the GAME system.

    Args:
        api_key (str): Authentication key for API access.
        name (str): Name of the agent.
        agent_goal (str): High-level goal or purpose of the agent.
        agent_description (str): Detailed description of the agent's capabilities.
        get_agent_state_fn (Callable): Function to retrieve agent's current state.

    The Agent class serves as the primary interface for:
    - Managing worker configurations
    - Handling task execution
    - Maintaining session state
    - Coordinating API interactions
    """
    def __init__(self,
                 api_key: str,
                 name: str,
                 agent_goal: str,
                 agent_description: str,
                 get_agent_state_fn: Callable,
                 workers: Optional[List[WorkerConfig]] = None,
                 ):

        if api_key.startswith("apt-"):
            self.client = GAMEClientV2(api_key)
        else:
            self.client = GAMEClient(api_key)

        self._api_key: str = api_key

        # checks
        if not self._api_key:
            raise ValueError("API key not set")

        # initialize session
        self._session = Session()

        # Input validation for character limits
        if len(agent_goal.replace(" ", "")) > 1500:
            raise ValueError("Agent goal must not exceed 1500 characters")
        if len(agent_description.replace(" ", "")) > 3000:
            raise ValueError("Agent description must not exceed 3000 characters")

        self.name = name
        self.agent_goal = agent_goal
        self.agent_description = agent_description

        # set up workers
        if workers is not None:
            self.workers = {w.id: w for w in workers}
        else:
            self.workers = {}
        self.current_worker_id = None

        # get agent/task generator state function
        self.get_agent_state_fn = get_agent_state_fn

        # initialize and set up agent states
        self.agent_state = self.get_agent_state_fn(None, None)

        # initialize observation
        observation_content = self.agent_state["observations"] if "observations" in self.agent_state else ""
        self.observation = {
            "content": observation_content,
            "is_global": True,
        }

        # create agent
        self.agent_id = self.client.create_agent(
            self.name, self.agent_description, self.agent_goal
        )

    def compile(self):
        """ Compile the workers for the agent - i.e. set up task generator"""
        if not self.workers:
            raise ValueError("No workers added to the agent")

        workers_list = list(self.workers.values())

        self._map_id = self.client.create_workers(workers_list)
        self.current_worker_id = next(iter(self.workers.values())).id

        # initialize and set up worker states
        worker_states = {}
        for worker in workers_list:
            dummy_function_result = FunctionResult(
                action_id="",
                action_status=FunctionResultStatus.DONE,
                feedback_message="",
                info={},
            )
            worker_states[worker.id] = worker.get_state_fn(
                dummy_function_result, self.agent_state)

        self.worker_states = worker_states

        return self._map_id

    def reset(self):
        """ Reset the agent session"""
        self._session.reset()

    def add_worker(self, worker_config: WorkerConfig):
        """Add worker to worker dict for the agent"""
        self.workers[worker_config.id] = worker_config
        return self.workers

    def get_worker_config(self, worker_id: str):
        """Get worker config from worker dict"""
        return self.workers[worker_id]

    def get_worker(self, worker_id: str):
        """Initialize a working interactable standalone worker"""
        worker_config = self.get_worker_config(worker_id)
        return Worker(
            api_key=self._api_key,
            # THIS DESCRIPTION IS THE AGENT DESCRIPTION/CHARACTER CARD - WORKER DESCRIPTION IS ONLY USED FOR THE TASK GENERATOR
            description=self.agent_description,
            instruction=worker_config.instruction,
            get_state_fn=worker_config.get_state_fn,
            action_space=worker_config.action_space,
        )

    def _get_action(
        self,
        function_result: Optional[FunctionResult] = None
    ) -> ActionResponse:

        # dummy function result if None is provided - for get_state_fn to take the same input all the time
        if function_result is None:
            function_result = FunctionResult(
                action_id="",
                action_status=FunctionResultStatus.DONE,
                feedback_message="",
                info={},
            )

        # set up payload
        data = {
            "location": self.current_worker_id,
            "map_id": self._map_id,
            "environment": self.worker_states[self.current_worker_id],
            "functions": [
                f.get_function_def()
                for f in self.workers[self.current_worker_id].action_space.values()
            ],
            "events": {},
            "agent_state": self.agent_state,
            "current_action": (
                function_result.model_dump(
                    exclude={'info'}) if function_result else None
            ),
            "observations": self.observation,
            "version": "v2",
        }

        # make API call
        response = self.client.get_agent_action(
            agent_id=self.agent_id,
            data=data,
        )

        return ActionResponse.model_validate(response)

    def step(self):

        # get next task/action from GAME API
        action_response = self._get_action(self._session.function_result)
        action_type = action_response.action_type

        print("#" * 50)
        print("STEP")
        print(f"Current Task: {action_response.agent_state.current_task}")
        print(f"Action response: {action_response}")
        print(f"Action type: {action_type}")

        # if new task is updated/generated
        if (
            action_response.agent_state.hlp
            and action_response.agent_state.hlp.change_indicator
        ):
            print("New task generated")
            print(f"Task: {action_response.agent_state.current_task}")

        # execute action
        if action_type in [
            ActionType.CALL_FUNCTION,
            ActionType.CONTINUE_FUNCTION,
        ]:
            print(f"Action Selected: {action_response.action_args['fn_name']}")
            print(f"Action Args: {action_response.action_args['args']}")

            if not action_response.action_args:
                raise ValueError("No function information provided by GAME")

            self._session.function_result = (
                self.workers[self.current_worker_id]
                .action_space[action_response.action_args["fn_name"]]
                .execute(**action_response.action_args)
            )

            print(f"Function result: {self._session.function_result}")

            # update worker states
            updated_worker_state = self.workers[self.current_worker_id].get_state_fn(
                self._session.function_result, self.worker_states[self.current_worker_id])
            self.worker_states[self.current_worker_id] = updated_worker_state

            update_observation = "worker"

        elif action_response.action_type == ActionType.WAIT:
            print("Task ended completed or ended (not possible with current actions)")
            update_observation = "task"

        elif action_response.action_type == ActionType.GO_TO:
            if not action_response.action_args:
                raise ValueError("No location information provided by GAME")

            next_worker = action_response.action_args["location_id"]
            print(f"Next worker selected: {next_worker}")
            self.current_worker_id = next_worker
            
            update_observation = "worker"
        else:
            raise ValueError(
                f"Unknown action type: {action_response.action_type}")

        # update agent state
        self.agent_state = self.get_agent_state_fn(
            self._session.function_result, self.agent_state)
        
        # update observation (saved state)
        if update_observation == "task":
            if "observations" in self.agent_state:
                observation_content = self.agent_state["observations"]
                self.observation = {
                    "content": observation_content,
                    "is_global": True,
                }
            else:
                self.observation = None
        elif update_observation == "worker":
            current_worker_state = self.worker_states[self.current_worker_id]
            if "observations" in current_worker_state:
                observation_content = current_worker_state["observations"]
                self.observation = {
                    "content": observation_content,
                    "is_global": False,
                }
            else:
                self.observation = {
                    "content": "",
                    "is_global": True
                }
        else:
            self.observation = {
                "content": "",
                "is_global": True
            }


    def run(self):
        self._session = Session()
        while True:
            self.step()
