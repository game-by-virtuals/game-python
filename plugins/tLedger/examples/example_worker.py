import os
import sys
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import FunctionResult
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env.example'
load_dotenv(dotenv_path=env_path)

# Add the project directory to the PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from plugins.tLedger.tledger_plugin_gamesdk.tLedger_plugin import TLedgerPlugin

def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on the function results
    """
    init_state = {}

    if current_state is None:
        return init_state

    # Update state with the function result info
    current_state.update(function_result.info)

    return current_state



tledger_plugin = TLedgerPlugin(
  api_key=os.environ.get("SENDER_TLEDGER_API_KEY"),
  api_secret=os.environ.get("SENDER_TLEDGER_API_SECRET"),
  api_url = os.environ.get("TLEDGER_API_URL")
)

# Create worker
tledger_worker = Worker(
    api_key=os.environ.get("GAME_API_KEY"),
    description="Worker specialized in doing payments on Tledger",
    get_state_fn=get_state_fn,
    action_space=tledger_plugin.get_tools(),
)

# # Run example query
queries = [
    "Get TLedger account details",
    "Create payment of 1 SOL using the TLedger account details. The receiving agent's ID is 'agt_3db52291-a9f8-4f04-a180-adb6e50ef5b0', the payment amount is 1, the settlement network is 'solana', the currency is 'sol', and the conversation ID is 'conv1'",
    "Get payment by ID. Retrieve the payment ID using the previous query",
]

for query in queries:
    print("-" * 100)
    print(f"Query: {query}")
    tledger_worker.run(query)
