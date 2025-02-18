"""Copied from compass.virtuals_sdk.simple_worker."""

from game_sdk.game.worker import Worker

from compass.virtuals_sdk.api_wrapper import AaveV3, Aerodrome, Others, UniswapV3
from compass.virtuals_sdk.config import api_key
from compass.virtuals_sdk.shared_defaults import get_state_fn
from compass.virtuals_sdk.wallet import Wallet

others_compass_api_worker = Worker(
    api_key=api_key,
    description=Others.worker_description,
    get_state_fn=get_state_fn,
    action_space=Others.action_space,
)
aave_compass_api_worker = Worker(
    api_key=api_key,
    description=AaveV3.worker_description,
    get_state_fn=get_state_fn,
    action_space=AaveV3.action_space,
)
aerodrome_compass_api_worker = Worker(
    api_key=api_key,
    description=Aerodrome.worker_description,
    get_state_fn=get_state_fn,
    action_space=Aerodrome.action_space,
)
uniswap_compass_api_worker = Worker(
    api_key=api_key,
    description=UniswapV3.worker_description,
    get_state_fn=get_state_fn,
    action_space=UniswapV3.action_space,
)
wallet_worker = Worker(
    api_key=api_key,
    description=Wallet.worker_description,
    get_state_fn=get_state_fn,
    action_space=Wallet.action_space,
)

query_and_worker_pairs = [
    ("Please tell me the details of the ens name vitalik.eth", others_compass_api_worker),
    ("Please get me the price of WBTC in USDC on the arbitrum network", aave_compass_api_worker),
    ("Please tell me the price of USDC/WETH on the arbitrum chain", uniswap_compass_api_worker),
    ("Please tell me my own wallet address", wallet_worker)
]
for query, worker in query_and_worker_pairs:
    print("\n\n")
    print(f"QUERY: {query}")
    print(f"WORKER: {worker.description}")
    worker.run(query)