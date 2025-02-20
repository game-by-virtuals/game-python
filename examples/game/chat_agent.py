import os
from typing import Any, Tuple
from game_sdk.game.chat_agent import ChatAgent
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus

# ACTION SPACE

def generate_picture(prompt: str) -> Tuple[FunctionResultStatus, str, dict[str, Any]]:
    print(f"Generated picture with prompt: {prompt}")
    return FunctionResultStatus.DONE, "Picture generated and presented to the user", {}

def generate_music(prompt: str) -> Tuple[FunctionResultStatus, str, dict[str, Any]]:
    print(f"Generated music with prompt: {prompt}")
    return FunctionResultStatus.DONE, "Music generated and presented to the user", {}


def check_crypto_price(currency: str):
    prices = {
        "bitcoin": 100000,
        "ethereum": 20000,
    }
    result = prices[currency.lower()]
    if result is None:
        return FunctionResultStatus.FAILED, "The price of the currency is not available", {}
    return FunctionResultStatus.DONE, f"The price of {currency} is {result}", {}


action_space = [
    Function(
        fn_name="generate_picture",
        fn_description="Generate a picture",
        args=[Argument(name="prompt", description="The prompt for the picture")],
        executable=generate_picture,
    ),
    Function(
        fn_name="generate_music",
        fn_description="Generate a music",
        args=[Argument(name="prompt", description="The prompt for the music")],
        executable=generate_music,
    ),
    Function(
        fn_name="check_crypto_price",
        fn_description="Check the price of a crypto currency",
        args=[Argument(name="currency", description="The currency to check the price of")],
        executable=check_crypto_price,
    ),
]

api_key = os.environ.get("GAME_API_KEY")
if not api_key:
    raise ValueError("GAME_API_KEY is not set")


# CREATE AGENT
agent = ChatAgent(
    prompt="You are helpful assistant",
    api_key=api_key
)

chat = agent.create_chat(
    partner_id="tom",
    partner_name="Tom",
    action_space=action_space,
)

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