from pydantic import BaseModel, Field
import requests
from typing import (
    Any,
    Dict,
    Generic,
    Literal,
    Sequence,
    TypeVar,
)

from game_sdk.game.custom_types import Function, FunctionResult


class StartTaskResponse(BaseModel):
    response_type: Literal["start_task"]
    reasoning: str
    task: str


class StepFailureResponse(BaseModel):
    response_type: Literal["step_failure"]


class FunctionCallResponseModel(BaseModel):
    fn_id: str
    fn_name: str
    fn_arguments: Dict[str, Any]


class CallFunctionResponse(BaseModel):
    response_type: Literal["call_function"] = Field(
        default="call_function", frozen=True
    )
    reasoning: str
    function: FunctionCallResponseModel


class FinishTaskResponse(BaseModel):
    response_type: Literal["finish_task"] = Field(default="finish_task", frozen=True)
    reasoning: str
    result: str


T = TypeVar("T", bound=BaseModel)


class AgentResponse(BaseModel, Generic[T]):
    data: T


class AutonomousAgentClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json", "x-api-key": self.api_key}

    def create_agent(self, description: str) -> str:
        """
        API call to create an agent instance (worker or agent with task generator)
        """
        payload = {"data": {"name": "", "goal": "", "description": description}}

        response = requests.post(
            f"{self.base_url}/agents", headers=self.headers, json=payload
        )

        return self._get_response_body(response)["data"]["id"]

    def create_session(self, agent_id: str, goal: str) -> str:
        response = requests.post(
            f"{self.base_url}/agent/{agent_id}/session",
            headers=self.headers,
            json={"goal": goal},
        )

        if response.status_code != 200:
            raise ValueError(
                f"Failed to get agent action (status {response.status_code}). Response: {response.text}"
            )

        response_json = response.json()

        return response_json["data"]["session_id"]

    def next_task(
        self, session_id: str, goal_state: str, action_space: Sequence[Function]
    ) -> StartTaskResponse | StepFailureResponse:
        response = requests.post(
            f"{self.base_url}/session/{session_id}/step",
            headers=self.headers,
            json={
                "goal_state": goal_state,
                "action_space": [f.get_function_def() for f in action_space],
            },
        )

        if response.status_code != 200:
            raise ValueError(
                f"Failed to get next task (status {response.status_code}). Response: {response.text}"
            )

        response_json = response.json()

        return (
            AgentResponse[StartTaskResponse | StepFailureResponse]
            .model_validate(response_json)
            .data
        )

    def start_task(
        self, session_id: str, environment_state: str, action_space: Sequence[Function]
    ) -> CallFunctionResponse | FinishTaskResponse | StepFailureResponse:
        response = requests.post(
            f"{self.base_url}/session/{session_id}/task/start",
            headers=self.headers,
            json={
                "environment_state": environment_state,
                "action_space": [f.get_function_def() for f in action_space],
            },
        )

        if response.status_code != 200:
            raise ValueError(
                f"Failed to start task (status {response.status_code}). Response: {response.text}"
            )

        response_json = response.json()

        return (
            AgentResponse[
                CallFunctionResponse | FinishTaskResponse | StepFailureResponse
            ]
            .model_validate(response_json)
            .data
        )

    def report_function_result(
        self,
        session_id: str,
        function_result: FunctionResult,
        environment_state: str,
        action_space: Sequence[Function],
    ) -> CallFunctionResponse | FinishTaskResponse | StepFailureResponse:
        response = requests.post(
            f"{self.base_url}/session/{session_id}/report",
            headers=self.headers,
            json={
                "function_result": function_result.model_dump(exclude={"info"}),
                "environment_state": environment_state,
                "action_space": [f.get_function_def() for f in action_space],
            },
        )

        if response.status_code != 200:
            raise ValueError(
                f"Failed to report function result (status {response.status_code}). Response: {response.text}"
            )

        response_json = response.json()

        return (
            AgentResponse[
                CallFunctionResponse | FinishTaskResponse | StepFailureResponse
            ]
            .model_validate(response_json)
            .data
        ) 

    def _get_response_body(self, response: requests.Response) -> dict[str, Any]:
        if response.status_code != 200:
            raise ValueError(
                f"Failed to get response body (status {response.status_code}). Response: {response.text}"
            )

        response_json = response.json()

        return response_json
