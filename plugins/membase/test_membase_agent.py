import os
from typing import Literal, Tuple
from game_sdk.game.custom_types import Function, FunctionResultStatus, Argument
from membase_plugin_gamesdk.membase_plugin_gamesdk import MembasePlugin
from game_sdk.game.chat_agent import Chat, ChatAgent


# set your own account and agent name
# or set environment variables
default_account = "game_sdk_test"
default_agent_name = "game_sdk_test_agent"
default_conversation_id = "67fd033a0740eed72502b65e"

game_api_key = os.environ.get("GAME_API_KEY")
chat_agent = ChatAgent(
    prompt="You are a helpful assistant.",
    api_key=game_api_key,
)

membase_plugin = MembasePlugin(
  account=default_account,
  agent_name=default_agent_name,
  auto_upload_to_hub=True,
  preload_from_hub=False,
)


def save_memory_executable(membase_plugin: MembasePlugin, memory: str, memory_type: Literal["user", "assistant"]) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        membase_plugin.add_memory(memory, memory_type)
        return FunctionResultStatus.DONE, "Memory added successfully", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}

def get_memory_executable(membase_plugin: MembasePlugin, recent_n: int = 10) -> Tuple[FunctionResultStatus, str, dict]:
    try:    
        memory = membase_plugin.get_memory(recent_n=recent_n)
        result = ""
        for msg in memory:
            result += f"{msg.role}: {msg.content}\n"
        return FunctionResultStatus.DONE, result, {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}

action_space = [
    Function(
        fn_name="save_memory",
        fn_description="Save a memory to the membase database",
        args=[
            Argument(name="memory", type="str", description="The memory to save"),
            Argument(name="memory_type", type=["user", "assistant"], description="The type of memory to save"),
        ],
        executable=lambda memory, memory_type: save_memory_executable(membase_plugin, memory, memory_type),
    ),
    Function(
        fn_name="get_memory",
        fn_description="Get the last n memories from the membase database",
        args=[
            Argument(name="recent_n", type="int", description="The number of memories to retrieve"),
        ],
        executable=lambda recent_n: get_memory_executable(membase_plugin, recent_n),
    )
]

chat = chat_agent.create_chat(
    partner_id=default_account,
    partner_name=default_agent_name,
    action_space=action_space,
)

membase_plugin.switch_conversation_id(default_conversation_id)
membase_plugin.reload_memory(default_conversation_id)

chat_continue = True
while chat_continue:

    user_message = input("Enter a message: ")

    response = chat.next(user_message)

    if response.function_call:
        print(f"Function call: {response.function_call.fn_name}")

    if response.message:
        print(f"Response: {response.message}")

    if response.is_finished:
        chat_continue = False
        break

print("Chat ended")

