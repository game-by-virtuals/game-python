from typing import Any, Callable, Dict, List, Optional, Tuple
from game_sdk.game.custom_types import (
    ChatResponse,
    FunctionCallResponse,
    FunctionResult,
    GameChatResponse,
    Function,
    AgentMessage,
)
from game_sdk.game.api_v2 import GAMEClientV2


class Chat:
    def __init__(
        self,
        conversation_id: str,
        client: GAMEClientV2,
        action_space: Optional[List[Function]] = None,
        get_state_fn: Optional[Callable[[], Dict[str, Any]]] = None,
    ):
        self.chat_id = conversation_id
        self.client = client
        self.action_space = (
            {f.fn_name: f for f in action_space} if action_space else None
        )
        self.get_state_fn = get_state_fn

    def next(self, message: str) -> ChatResponse:

        convo_response = self._update_conversation(message)

        # execute functions/actions if present
        if convo_response.function_call:
            if not self.action_space:
                raise Exception("No functions provided")

            fn_name = convo_response.function_call.fn_name

            fn_to_call = self.action_space.get(fn_name)
            if not fn_to_call:
                raise Exception(
                    f"Function {fn_name}, returned by the agent, not found in action space"
                )

            result = fn_to_call.execute(
                **{
                    "fn_id": convo_response.function_call.id,
                    "args": convo_response.function_call.args,
                }
            )
            response_message = self._report_function_result(result)
            function_call_response = FunctionCallResponse(
                fn_name=fn_name,
                fn_args=convo_response.function_call.args,
                result=result,
            )
        else:
            response_message = convo_response.message or ""
            function_call_response = None

        return ChatResponse(
            message=response_message,
            is_finished=convo_response.is_finished,
            function_call=function_call_response,
        )

    def end(self, message: Optional[str] = None):
        self.client.end_chat(
            self.chat_id,
            {
                "message": message,
            },
        )

    def _update_conversation(self, message: str) -> GameChatResponse:
        data = {
            "message": message,
            "state": self.get_state_fn() if self.get_state_fn else None,
            "functions": (
                [f.get_function_def() for f in self.action_space.values()]
                if self.action_space
                else None
            ),
        }
        result = self.client.update_chat(self.chat_id, data)
        return GameChatResponse.model_validate(result)

    def _report_function_result(self, result: FunctionResult) -> str:
        data = {
            "fn_id": result.action_id,
            "result": (
                f"{result.action_status.value}: {result.feedback_message}"
                if result.feedback_message
                else result.action_status.value
            ),
        }
        response = self.client.report_function(self.chat_id, data)

        message = response.get("message")
        if not message:
            raise Exception("Agent did not return a message for the function report.")
        return message


class ChatAgent:
    def __init__(
        self,
        api_key: str,
        prompt: str,
    ):
        self._api_key = api_key
        self.prompt = prompt

        if api_key.startswith("apt-"):
            self.client = GAMEClientV2(api_key)
        else:
            raise Exception("Please use V2 API key to use ChatAgent")

    def create_chat(
        self,
        partner_id: str,
        partner_name: str,
        action_space: Optional[List[Function]] = None,
        get_state_fn: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> Chat:

        chat_id = self.client.create_chat(
            {
                "prompt": self.prompt,
                "partner_id": partner_id,
                "partner_name": partner_name,
            },
        )

        return Chat(chat_id, self.client, action_space, get_state_fn)
