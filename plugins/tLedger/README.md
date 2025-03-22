# TLedger Plugin for GAME SDK

## Features

- get_agent_details - Get the details of your agent, including the TLedger agent_id and the balances of the agent's wallets
- create_payment - Create a payment request for a specific amount and currency
- get_payment_by_id - Get the details of a payment request by its ID
- get_payments - Get a list of all payments

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

1. You first need to register your user on the TLedger platform

POST /api/v1/users/signup
payload = {
  "email": "user@example.com",
  "password": "password",
  "full_name": "full name"
}

2. Login to your account and obtain the JWT token

POST /api/v1/login/access-token
payload = {
    "username": "user@example.com",
    "password": "password"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

### TLedger Project Setup

1. Create a project

POST /api/v1/projects
payload = {
  "user_profile_id": "usr_123", # user_profile_id from the user profile
  "network": "solana",
  "description": "Solana Launch Pad",
  "name": "Twitter Project",
  "daily_limit": 100
}

### TLedger Agent Profile Setup

1. Create an agent profile

POST /api/v1/agent_profiles
payload = {
  "project_id": "{{project_id}}",
  "name": "My Agent",
  "description": "Twitter KOL Agent"
}

### TLedger Key Setup for Agent

1. You need to create an API key for the agent to use the TLedger APIs

POST /api/v1/api_key/generate-api-key
{
  "scopes": ["payments:read", "payments:write", "payments:agent:read"],
  "agent_id": "agt_123456",
  "created_by": "Name"
}

For a complete list of TLedger APIs, please feel free to look at the public documentation at: https://docs.t54.ai/

### Setup and Configuration

Import and initialize the plugin to use in your worker:

```python
import os
from plugins.tLedger.tledger_plugin_gamesdk.t54_payments_plugin import T54PaymentsPlugin
from plugins.tLedger.tledger_plugin_gamesdk.t54_account_details_plugin import T54AccountDetailsPlugin

account_details_plugin = T54AccountDetailsPlugin(
  api_key=os.environ.get("TLEDGER_API_KEY"),
  api_secret=os.environ.get("TLEDGER_API_SECRET"),
  api_url=os.environ.get("TLEDGER_API_URL")
)

payments_plugin = T54PaymentsPlugin(
  api_key=os.environ.get("TLEDGER_API_KEY"),
  api_secret=os.environ.get("TLEDGER_API_SECRET"),
  api_url = os.environ.get("TLEDGER_API_URL")
)
```

**Basic worker example:**

```python

def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:

tledger_worker = Worker(
    api_key=os.environ.get("GAME_API_KEY"),
    description="Worker specialized in doing payments on Tledger",
    get_state_fn=get_state_fn,
    action_space=[
        account_details_plugin.functions.get("get_agent_profile_details"),
        payments_plugin.functions.get("create_payment"),
        payments_plugin.functions.get("get_payment_by_id"),
    ],
)

tledger_worker.run("Get TLedger account details")
```
