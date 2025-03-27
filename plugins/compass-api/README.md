# CompassLabs API Plugin for GAME SDK

The [CompassLabs](https://compasslabs.ai) API offers interaction with many DeFi protocols across multiple chains. It can retrieve human-readable information from the chain (presenting information such as annulalised yields so that your agent does not need to derive it), and build transactions that your agent can then sign and send using the simple wallet executable.

You can directly run the executables within the plugin, use the suggested worker configs, or integrate the executables however you like.

It is possible to use the executables on more than one chain simulataneously, however this is in beta.

## Installation
From this directory (`compass-api`), run the installation:
```bash
pip install -e .
```

## Usage
1. If you don't already have one, create a wallet, and get its private key.
2. Get a RPC node to submit transactions to. (There are many free ones, including within Metamask settings.)
3. Create a project app, generate the following credentials and set the following environment variables (e.g. using a `.bashrc` or a `.zshrc` file):
  - `ETHEREUM_RPC_URL`
  - `ETHEREUM_PRIVATE_KEY`
  - `GAME_API_KEY`

4. Import and use the plugin.
```python
# You can directly run our sample agent:
from compasslabs_api_plugin_gamesdk.compasslabs_plugin import *

simple_agent.compass_agent.compile()
simple_agent.compass_agent.run()
```
OR
```python
# You can use the example workers:
from compasslabs_api_plugin_gamesdk.compasslabs_plugin import *

simple_workers.others_compass_api_worker.run("get the details of the ENS name vitalik.eth")
```
OR
```python
# You can use the functions to construct your own workers:
from game_sdk.game.agent import Agent, WorkerConfig

from compass.api_client import Chain
from compass.virtuals_sdk.api_wrapper import (
    AaveV3,
    Aerodrome,
    Others,
    UniswapV3,
)
from compass.virtuals_sdk.config import api_key
from compass.virtuals_sdk.shared_defaults import get_state_fn
from compass.virtuals_sdk.wallet import Wallet

available_chains = [i.value for i in Chain]
worker_instruction = "Interact with your assigned defi protocol."

compass_agent = Agent(
    api_key=api_key,
    name="A defi agent that can operate on multiple defi exchanges",
    agent_goal=f"Make some money. Your ethereum wallet address is can be obtained via the wallet worker.When you need to set the sender or user of a transaction request, set if to to your wallet address. When you must choose between chains, choose one of {available_chains}",
    agent_description="defi agent",
    get_agent_state_fn=get_state_fn,
    workers=[
        WorkerConfig(cls.id, cls.worker_description, cls.get_state_fn, cls.action_space)
        for cls in [Wallet, Aerodrome, AaveV3, Others, UniswapV3]
    ],
)

compass_agent.compile()
compass_agent.run()

```