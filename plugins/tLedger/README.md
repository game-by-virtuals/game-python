# TLedger Plugin for GAME SDK

## Features

- get_agent_details - Get the details of your agent, including the TLedger agent_id and the balances of the agent's wallets
- create_payment - Create a payment request for a specific amount and currency
- get_payment_by_id - Get the details of a payment request by its ID

## Admin Setup for doing agent to agent payments using TLedger Plugin

You are required to set up your account, project, agent profile, and keys in the TLedger platform to use the TLedger plugin for GAME SDK.

To make the setup easy, all you need to do is run the setup.py file in the tLedger plugin folder. This will install the plugin and set up the necessary environment variables for you.
To set up the necessary environment variables, please fill in thw details in the .env.setup file

```shell
python3 ./setup.py
```
There are also two agents set for you incase you want to test the plugin. The agent details are as follows:

Agent 1:
- Agent ID: agt_59b17650-a689-4649-91fa-4bf5d0db56ad
- key: ewSZjNQGPLle-vn5dMZoLOGUljEB6fbmox31o7KLKuI
- secret: iqB7-iETCVBE0UV_0HfRAwCHkVXO9_4cCPJYmTIyUpHauHlVP4Hk5xSsCquRqBO_2_eQ6OK_Zu7P1X4LU7hSHg

Agent 2:
- Agent ID: agt_3db52291-a9f8-4f04-a180-adb6e50ef5b0
- key: j06KtBcRRbmrEAqIVSiXZc3DPAJSqymDimo__ERD0oQ
- secret: h13ERQG797cYMeNeRLvwDF_3-DBt4o-kp0fL-bFHKstTUTS5xsLUFgDEUZG2GsoEKINxeSVusbAQxc24mHm1eQ

### TLedger Account Setup
For a complete list of TLedger setup APIs, please feel free to look at the public documentation at: https://docs.t54.ai/

### Toolkit Setup and Configuration

Import and initialize the plugin to use in your worker:

```python
import os
from plugins.tLedger.tledger_plugin_gamesdk.tLedger_plugin import TLedgerPlugin

tledger_plugin = TLedgerPlugin(
  api_key=os.environ.get("SENDER_TLEDGER_API_KEY"),
  api_secret=os.environ.get("SENDER_TLEDGER_API_SECRET"),
  api_url=os.environ.get("TLEDGER_API_URL")
)
```

**Basic worker example:**

```python

def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:

tledger_worker = Worker(
    api_key=os.environ.get("GAME_API_KEY"),
    description="Worker specialized in doing payments on Tledger",
    get_state_fn=get_state_fn,
    action_space=tledger_plugin.get_tools(),
)

tledger_worker.run("Get TLedger account details")
```
