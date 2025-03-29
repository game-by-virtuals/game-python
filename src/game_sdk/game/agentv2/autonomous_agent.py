from dataclasses import dataclass
import json
from typing import Callable, Sequence

from game_sdk.game.agentv2.autonomous_agent_client import AutonomousAgentClient, CallFunctionResponse, FinishTaskResponse, StartTaskResponse, StepFailureResponse
from game_sdk.game.custom_types import Function, FunctionResult


@dataclass(frozen=True)
class Session:

    def step(self) -> None:
        pass


class IdleState:
    pass


class TaskPendingState:
    pass

@dataclass(frozen=True)
class TaskRunningState:
    result: FunctionResult

class StepFailedException(Exception):
    pass


AgentState = IdleState | TaskPendingState | TaskRunningState


class Agent:
    def __init__(
        self,
        description: str,
        goal: str,
        api_key: str,
        action_space: Sequence[Function],
        read_environment_fn: Callable[[], str],
        read_goal_state_fn: Callable[[], str],
        base_url: str,
    ):
        self.description = description
        self.goal = goal
        self.api_key = api_key
        self.action_space = {fn.fn_name: fn for fn in action_space}
        self.client = AutonomousAgentClient(api_key, base_url)
        self.read_environment_fn = read_environment_fn
        self.read_goal_state_fn = read_goal_state_fn
        self.agent_id = self.client.create_agent(self.description)
        self.session_id = self.client.create_session(self.agent_id, self.goal)
        self.state: AgentState = IdleState()

    def step(self) -> None:
        try:
            match self.state:
                case IdleState():
                    print("\n\n### Requesting next task.")
                    response = self.client.next_task(
                        self.session_id, self.read_goal_state_fn(), list(self.action_space.values())
                    )
                    match response:
                        case StartTaskResponse():
                            print(f"\n\n### Reasoning: \n {response.reasoning}")
                            print(f"\n\n### Task assigned: \n {response.task}")
                            self.state = TaskPendingState()
                        case StepFailureResponse():
                            raise StepFailedException()
                case TaskPendingState():
                    print("\n\n### Starting task.")
                    response = self.client.start_task(
                        self.session_id, self.read_environment_fn(), list(self.action_space.values())
                    )
                    self._handle_task_execution_response(response)
                case TaskRunningState():
                    print(f"\n\n### Reporting function result")
                    response = self.client.report_function_result(
                        self.session_id, self.state.result, self.read_environment_fn(), list(self.action_space.values())
                    )
                    self._handle_task_execution_response(response)

        except StepFailedException:
            print("Step failed")

    def _handle_task_execution_response(self, response: CallFunctionResponse | FinishTaskResponse | StepFailureResponse) -> None:
        match response:
            case CallFunctionResponse():
                print(f"\n\n### Reasoning: \n {response.reasoning}")
                print(f"\n\n### Call function: \n {response.function.fn_name}({response.function.fn_arguments})")
                fn = self.action_space[response.function.fn_name]
                result = fn.execute(**{
                    "fn_id": response.function.fn_id,
                    "args": response.function.fn_arguments
                })
                print(f"\n\n### Function result: \n {json.dumps(result.model_dump(), indent=2)}")
                self.state = TaskRunningState(result)
            case FinishTaskResponse():
                print(f"\n\n### Reasoning: \n {response.reasoning}")
                print(f"\n\n### Task finished: \n {response.result}")
                self.state = IdleState()
            case StepFailureResponse():
                raise StepFailedException()