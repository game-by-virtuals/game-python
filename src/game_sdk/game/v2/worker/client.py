from dataclasses import dataclass
from typing import Any, Dict, Generic, Literal, Sequence, TypeVar

from pydantic import BaseModel
import requests

from game_sdk.game.custom_types import Function


class StepFailureResponse(BaseModel):
    type: Literal["step_failed"]


class FunctionCallResponse(BaseModel):
    type: Literal["call_function"]
    fn_id: str
    fn_name: str
    fn_args: Dict[str, Any]


class FinalAnswerResponse(BaseModel):
    type: Literal["final_answer"]
    result: str

WorkerResponse = StepFailureResponse | FunctionCallResponse | FinalAnswerResponse


class IdleStateResponse(BaseModel):
    type: Literal["idle"]


T = TypeVar("T", bound=BaseModel)


class WorkerGenericResponse(BaseModel, Generic[T]):
    data: T


@dataclass(frozen=True)
class WorkerClient:
    api_key: str
    base_url: str

    def create_session(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/v2/worker/sessions", json={"prompt": prompt},
            headers={
                "X-API-Key": self.api_key,
            }
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to update conversation (status {response.status_code}). Response: {response.text}"
            )

        response_json = response.json()
        return response_json["session_id"]

    def send_message(
        self,
        session_id: str,
        message: str,
        state: str,
        action_space: Sequence[Function],
        model_name: str,
    ) -> WorkerResponse:
        response = requests.post(
            f"{self.base_url}/v2/worker/sessions/{session_id}/message",
            json={
                "task": message,
                "state": state,
                "action_space": [f.get_function_def() for f in action_space],
            },
            headers={
                "X-API-KEY": self.api_key,
                "model_name": model_name,
            }
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to update conversation (status {response.status_code}). Response: {response.text}"
            )

        response_json = response.json()
        return (
            WorkerGenericResponse[WorkerResponse]
            .model_validate(response_json)
            .data
        )
    
    def ping(self, session_id: str, model_name: str) -> WorkerResponse | IdleStateResponse:
        response = requests.post(
            f"{self.base_url}/v2/worker/sessions/{session_id}/ping",
            headers={
                "X-API-KEY": self.api_key,
                "model_name": model_name,
            }
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to update conversation (status {response.status_code}). Response: {response.text}"
            )
        
        response_json = response.json()
        return (
            WorkerGenericResponse[WorkerResponse | IdleStateResponse]
            .model_validate(response_json)
            .data
        )
    
    def report_result(
        self,
        session_id: str,
        result: str,
        action_id: str,
        action_space: Sequence[Function],
        state: str,
        model_name: str,
    ) -> WorkerResponse:
        response = requests.post(
            f"{self.base_url}/v2/worker/sessions/{session_id}/result",
            json={
                "result": result,
                "fn_id": action_id,
                "action_space": [f.get_function_def() for f in action_space],
                "state": state,
            },
            headers={
                "X-API-KEY": self.api_key,
                "model_name": model_name,
            }
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to update conversation (status {response.status_code}). Response: {response.text}"
            )

        response_json = response.json()
        return (
            WorkerGenericResponse[WorkerResponse]
            .model_validate(response_json)
            .data
        )
