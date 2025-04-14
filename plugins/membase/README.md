# Membase Plugin for GAME SDK

A plugin for interacting with membase protocol through the GAME SDK.

## Description

Membase is a core component of the Unibase ecosystem. It stores historical information, interaction records, and persistent data of Agents, ensuring their continuity and traceability.

The membase plugin enables seamless integration with the membase protocol for decentralized storage. It provides functionality to upload memory to and reload it from the Unibase DA network.

- support conversation switch
- support conversation pesistence, upload if auto_upload_to_hub is set, conversation content can be visit at: https://testnet.hub.membase.io/
- support conversation preload from membase hub: https://testnet.hub.membase.io/

## Installation

```bash
pip install -e plugins/membase
```

## Configuration

The plugin requires the following environment variables to be set:

```shell
MEMBASE_HUB=<Membase hub endpoint, default is 'https://testnet.hub.membase.io' >
MEMBASE_ACCOUNT=<Membase account address>
MEMBASE_ID=<your agent name>
```

## Usage

```python
import time
import uuid
from membase_plugin_gamesdk.membase_plugin_gamesdk import MembasePlugin

# set your own account and agent name
# or set environment variables
default_account = "game_sdk_test"
default_agent_name = "game_sdk_test_agent"
membase_plugin = MembasePlugin(
  account=default_account,
  agent_name=default_agent_name,
  auto_upload_to_hub=True,
  preload_from_hub=True,
)

membase_plugin.add_memory("Hello, world!")
new_conversation_id = str(uuid.uuid4())
membase_plugin.switch_conversation_id(new_conversation_id)
membase_plugin.add_memory("Hello, world! 2")
```

more in `test_membase.py` file
