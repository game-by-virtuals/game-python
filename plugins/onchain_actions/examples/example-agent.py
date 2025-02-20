import os
from dotenv import load_dotenv
from pathlib import Path
from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import FunctionResult
from onchain_actions_game_sdk.onchain_actions import get_onchain_actions
from goat_plugins.erc20.token import PEPE, USDC
from goat_plugins.erc20 import ERC20PluginOptions, erc20

from web3 import Web3
from web3.middleware.signing import construct_sign_and_send_raw_middleware
from eth_account.signers.local import LocalAccount
from eth_account import Account
from goat_plugins.uniswap import uniswap, UniswapPluginOptions
from goat_wallets.web3 import Web3EVMWalletClient

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

def get_agent_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on the function results
    """
    init_state = {}

    if current_state is None:
        return init_state

    if function_result.info is not None:
        # Update state with the function result info
        current_state.update(function_result.info)

    return current_state

def get_worker_state(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on the function results
    """
    init_state = {}

    if current_state is None:
        return init_state

    if function_result.info is not None:
        # Update state with the function result info
        current_state.update(function_result.info)

    return current_state


# Initialize Web3 and account
w3 = Web3(Web3.HTTPProvider(os.environ.get("RPC_PROVIDER_URL")))
private_key = os.environ.get("WALLET_PRIVATE_KEY")
assert private_key is not None, "You must set WALLET_PRIVATE_KEY environment variable"
assert private_key.startswith("0x"), "Private key must start with 0x hex prefix"

account: LocalAccount = Account.from_key(private_key)
w3.eth.default_account = account.address  # Set the default account
w3.middleware_onion.add(
    construct_sign_and_send_raw_middleware(account)
)  # Add middleware

# Initialize tools with web3 wallet and Uniswap plugin
uniswap_api_key = os.environ.get("UNISWAP_API_KEY")
uniswap_base_url = os.environ.get("UNISWAP_BASE_URL", "https://trade-api.gateway.uniswap.org/v1")
assert uniswap_api_key is not None, "You must set UNISWAP_API_KEY environment variable"
assert uniswap_base_url is not None, "You must set UNISWAP_BASE_URL environment variable"

actions = get_onchain_actions(
        # You can also use other wallet types, such as Solana, etc.
        # See an example [here](https://github.com/goat-sdk/goat/blob/main/python/examples/solana/wallet/example.py)
        wallet=Web3EVMWalletClient(w3),
        plugins=[
            # Add any plugin you'd want to use here. You can see a list of all available 
            # plugins in Python [here](https://github.com/goat-sdk/goat/tree/main/python#plugins)
            #
            # Swap tokens with Uniswap or Jupiter, get info from CoinGecko, etc.
            erc20(options=ERC20PluginOptions(tokens=[USDC, PEPE])),
            uniswap(options=UniswapPluginOptions(
                api_key=uniswap_api_key,
                base_url=uniswap_base_url
            )),
        ],
    )

# Create worker
onchain_actions_worker = WorkerConfig(
    id="onchain_actions_worker",
    worker_description="Worker that executes onchain actions such as swaps, transfers, etc.",
    get_state_fn=get_worker_state,
    action_space=actions,
)

# Initialize the agent
agent = Agent(
    api_key=os.environ.get("GAME_API_KEY"),
    name="Onchain Actions Agent",
    agent_goal="Swap 0.01 USDC to PEPE",
    agent_description=(
        "An agent that executes onchain actions"
    ),
    get_agent_state_fn=get_agent_state_fn,
    workers=[
        onchain_actions_worker,
    ]
)

agent.compile()
agent.run()
