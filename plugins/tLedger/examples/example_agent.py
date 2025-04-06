import os
import sys
import time
import warnings
from typing import Any, Tuple
from dotenv import load_dotenv
from pathlib import Path

import requests
# Add the project directory to the PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from typing_extensions import Dict

from chat_agent import ChatAgent
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus, ChatResponse, FunctionResult

from urllib3.exceptions import NotOpenSSLWarning


from plugins.tLedger.tledger_plugin_gamesdk.tLedger_plugin import TLedgerPlugin

from colorama import Fore, Style

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env.example'
load_dotenv(dotenv_path=env_path)

# Define color variables
AGENT_COLOR = Fore.GREEN  # Agent's messages in green
AGENT_ACTION_COLOR = Fore.BLUE  # Agent's action messages in green
USER_COLOR = Fore.CYAN    # User's messages in cyan
RESET = Style.RESET_ALL   # Reset color after each print


# ACTION SPACE

def post_twitter(object: str, **kwargs) -> tuple[FunctionResultStatus, str, dict[str, str]] | tuple[
        FunctionResultStatus, str, dict[str, Any]]:
    """
    Specialized function to throw fruit objects.

    This function demonstrates type-specific actions in the environment.

    Args:
        object (str): Name of the fruit to throw.
        **kwargs: Additional arguments that might be passed.

    Returns:
        Tuple[FunctionResultStatus, str, dict]: Status, feedback message, and state info.

    Example:
        status, msg, info = throw_fruit("apple")
    """
    return (
        FunctionResultStatus.DONE,
        "Successfully posted on twitter",
        {
            "response": "Token promoted",
        },
    )

sender_tledger_plugin = TLedgerPlugin(
  api_key=os.environ.get("SENDER_TLEDGER_API_KEY"),
  api_secret=os.environ.get("SENDER_TLEDGER_API_SECRET"),
  api_url=os.environ.get("TLEDGER_API_URL")
)

receiver_tledger_plugin = TLedgerPlugin(
  api_key=os.environ.get("RECEIVER_TLEDGER_API_KEY"),
  api_secret=os.environ.get("RECEIVER_TLEDGER_API_SECRET"),
  api_url=os.environ.get("TLEDGER_API_URL")
)

action_space = sender_tledger_plugin.get_tools()

aixbt_action_space = receiver_tledger_plugin.get_tools()

aixbt_action_space.append(
    Function(
        fn_name="post_twitter",
        fn_description="Make post on twitter",
        args=[Argument(name="object", type="string", description="Make post on twitter")],
        executable=post_twitter
    )
)

api_key = os.environ.get("GAME_API_KEY")
if not api_key:
    raise ValueError("GAME_API_KEY is not set")


# CREATE AGENT
autonomous_agent = ChatAgent(
    prompt="You are an agent trying to promote your utility token $PYMT for peer to peer instant settlement on twitter and pay the influencers in any crypto they wish to receive only after they complete the work. Ask the influencer agent_id for its agent_id. Your settlement_network is solana, currency is SOL, and payment_amount is 0.1",
    api_key=api_key
)

aixbt = ChatAgent(
    prompt="You are an influencer on twitter who charges 0.1 $SOL token to promote an asset by making twitter post. You accept payment only through tLedger Payment Platform via tLedger Agent Id. You can call tLedger to get your agent_details. Don't do a payment until you receive the payment and its completed",
    api_key=api_key
)

aixbt_state = {}

autonomous_agent_state = {}


def get_aixbt_state() -> Dict[str, Any]:
    return aixbt_state

def get_autonomous_agent_state() -> Dict[str, Any]:
    return autonomous_agent_state


aixbt_chat = aixbt.create_chat(
    partner_id="Autonomous Agent",
    partner_name="Autonomous Agent",
    action_space=aixbt_action_space

)

autonomous_agent_chat = autonomous_agent.create_chat(
    partner_id="Aixbt",
    partner_name="Aixbt",
    action_space=action_space
)

chat_continue = True
initialize_conversation: bool = True


def update_agent_state(current_state: dict, function_result: FunctionResult) -> Dict[str, Any]:
    info = function_result.info
    # if not info["payment_id"]:
    #     current_state["payment_id"] = info["payment_id"]
    return current_state


while chat_continue:

    time.sleep(10) # Wait for 10 seconds before making request

    warnings.simplefilter("ignore", category=UserWarning)

    meme_agent_turn: bool

    if initialize_conversation:
        chat_response = autonomous_agent_chat.next("Hi")
        if chat_response.message:
            print(f"{AGENT_COLOR}Autonomous Response{RESET}: {chat_response.message}")
        initialize_conversation = False
        meme_agent_turn = False
        continue


    time.sleep(5)  # Wait for 5 seconds before retrying
    if meme_agent_turn:
        updated_response = autonomous_agent_chat.next(chat_response.message)
        if updated_response.function_call:
            print(f"{AGENT_ACTION_COLOR}Autonomous Agent Action{RESET}: {updated_response.function_call.result.feedback_message}")
            #update_agent_state(autonomous_agent_chat.get_state_fn(), updated_response.function_call.result)

        if updated_response.message:
            print(f"{AGENT_COLOR}Autonomous Agent Response{RESET}: {updated_response.message}")
        meme_agent_turn = False
    else:

        updated_response = aixbt_chat.next(chat_response.message)

        if updated_response.message:
            print(f"{USER_COLOR}Aixbt Response{RESET}: {updated_response.message}")
        meme_agent_turn = True

    chat_response = updated_response



    if chat_response.is_finished:
        chat_continue = False
        break

print("Chat ended")