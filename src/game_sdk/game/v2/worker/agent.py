from typing import Sequence, List, Dict, Any
from game_sdk.game.custom_types import Function
from game_sdk.game.v2.worker.client import (
    FinalAnswerResponse,
    FunctionCallResponse,
    IdleStateResponse,
    StepFailureResponse,
    WorkerClient,
)

RETRY_ATTEMPTS = 0


class WorkerAgent:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        prompt: str,
        action_space: Sequence[Function],
        model_name: str,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._prompt = prompt
        self._action_space = {f.fn_name: f for f in action_space}
        self._client = WorkerClient(api_key, base_url)
        self._session_id = self._client.create_session(prompt)
        self._model_name = model_name

    def get_session(self) -> str:
        return self._session_id

    def send_message(self, message: str) -> str:
        print(f"USER MESSAGE: {message}")
        agent_response = self._send_message(message)
        while isinstance(agent_response, FunctionCallResponse):
            function_to_call = self._action_space[agent_response.fn_name]
            print(f"ACTION: {agent_response.model_dump()}")
            function_call_result = function_to_call.execute(
                **{"fn_id": agent_response.fn_id, "args": agent_response.fn_args}
            )
            print(f"OBSERVATION: {function_call_result.feedback_message}")
            agent_response = self._report_result(
                f"API output: {function_call_result.feedback_message}" if function_call_result.feedback_message
                else function_call_result.action_status.value,
                function_call_result.action_id,
            )

        return agent_response.result

    def ping(self) -> FunctionCallResponse | FinalAnswerResponse | IdleStateResponse:
        agent_response = self._client.ping(self._session_id, self._model_name)
        match agent_response:
            case StepFailureResponse():
                raise Exception("Step failed.")
            case _:
                return agent_response

    # Private methods

    def _send_message(self, message: str) -> FunctionCallResponse | FinalAnswerResponse:
        attempts = 0
        while True and attempts < 1 + RETRY_ATTEMPTS:
            agent_response = self._client.send_message(
                self._session_id,
                message,
                "",
                list(self._action_space.values()),
                self._model_name,
            )
            match agent_response:
                case StepFailureResponse():
                    attempts += 1
                case _:
                    return agent_response

        raise Exception("Step failed.")

    def _report_result(
        self, result: str, action_id: str
    ) -> FunctionCallResponse | FinalAnswerResponse:
        attempts = 0
        while True and attempts < 1 + RETRY_ATTEMPTS:
            agent_response = self._client.report_result(
                self._session_id,
                result,
                action_id,
                list(self._action_space.values()),
                "",
                self._model_name,
            )
            match agent_response:
                case StepFailureResponse():
                    attempts += 1
                case _:
                    return agent_response

        raise Exception("Step failed.")
