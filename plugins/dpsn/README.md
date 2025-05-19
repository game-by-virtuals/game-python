# 🌐 DPSN Plugin for Virtuals Protocol (Python)

> Decentralized Publish-Subscribe Network (DPSN) plugin for Virtuals Protocol agents, implemented in Python.

[![Virtuals Protocol](https://img.shields.io/badge/Virtuals%20Protocol-plugin-blue)](https://virtuals.io/)
[![Version](https://img.shields.io/badge/version-alpha-orange)](https://github.com/virtuals-protocol/virtuals-game-python)
[![License](https://img.shields.io/badge/license-MIT-green)](../../LICENSE)

## 📋 Overview

This plugin enables Virtuals Protocol agents (written in Python) to connect to, subscribe to, and interact with data streams available on the [DPSN Data Streams Store](https://streams.dpsn.org/).

Agents can leverage this plugin to consume real-time data for decision-making, reacting to events, or integrating external information feeds.

To provide personalized data streams for your agents, you can create and publish data into your own DPSN topics using the [dpsn-client for Python](https://github.com/DPSN-org/dpsn-python-client).

For more information, visit:
-   [DPSN Official Website](https://dpsn.org)

## ✨ Features

-   **Seamless Integration**: Connects Virtuals Protocol agents (Python) to the DPSN decentralized pub/sub network.
-   **Real-time Data Handling**: Subscribe to topics and process incoming messages via a configurable callback.
-   **Topic Management**: Provides agent-executable functions to `subscribe` and `unsubscribe` from DPSN topics.
-   **Error Handling**: Includes basic error handling and logging for connection and subscription issues.
-   **Graceful Shutdown**: Allows the agent to explicitly shut down the DPSN connection.

## ⚙️ Configuration

Ensure the following environment variables are set, typically in a `.env` file in your project root:

> **Note**: The EVM private key (`PVT_KEY`) is used solely for signing authentication messages with the DPSN network. This process does not execute any on-chain transactions or incur gas fees.

```dotenv
# Your EVM-compatible wallet private key (e.g., Metamask)
PVT_KEY=your_evm_wallet_private_key_here

# The URL of the DPSN node to connect to (e.g., betanet.dpsn.org)
DPSN_URL=betanet.dpsn.org

# Optional: Add VIRTUALS_API_KEY if required by your GameAgent setup
# VIRTUALS_API_KEY=your_virtuals_api_key_here
```

## 📚 Usage

### Basic Setup 

The `DpsnPlugin` is designed to be used within the Virtuals Protocol Game SDK framework. You would typically instantiate it and potentially pass it to your `GameAgent` or similar construct.

```python
# Import the pre-instantiated plugin (recommended)
from plugins.dpsn.dpsn_plugin_gamesdk.dpsn_plugin import DpsnPlugin
load_dotenv()

dpsn_plugin=DpsnPlugin(
            dpsn_url=os.getenv("DPSN_URL"),
            pvt_key=os.getenv("PVT_KEY")
        )

# Define a simple message handler
def handle_message(message_data):
    topic = message_data.get('topic', 'unknown')
    payload = message_data.get('payload', {})
    print(f"Message on {topic}: {payload}")

# Register the message handler
dpsn_plugin.set_message_callback(handle_message)

# Subscribe to a topic
status, message, details = dpsn_plugin.subscribe(
    topic="0xe14768a6d8798e4390ec4cb8a4c991202c2115a5cd7a6c0a7ababcaf93b4d2d4/BTCUSDT/ticker"
)
print(f"Subscription status: {status}, Message: {message}")

# Later when done:
dpsn_plugin.unsubscribe(topic="0xe14768a6d8798e4390ec4cb8a4c991202c2115a5cd7a6c0a7ababcaf93b4d2d4/BTCUSDT/ticker")
dpsn_plugin.shutdown()

```

### Interacting via Agent Tasks

The Game Agent interacts with the plugin by executing tasks that map to the plugin's `Function` objects. The exact syntax depends on your Game SDK's `runTask` or equivalent method.

```python
from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import FunctionResult
from dpsn_plugin_gamesdk.dpsn_plugin import DpsnPlugin

load_dotenv()

dpsn_plugin=DpsnPlugin(
            dpsn_url=os.getenv("DPSN_URL"),
            pvt_key=os.getenv("PVT_KEY")
        )
# --- Add Message Handler --- 
def handle_incoming_message(message_data: dict):
    """Callback function to process messages received via the plugin."""
    try:
        topic = message_data.get('topic', 'N/A')
        payload = message_data.get('payload', '{}')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n--- Message Received ({timestamp}) ---")
        print(f"Topic: {topic}")
        # Pretty print payload if it's likely JSON/dict
        if isinstance(payload, (dict, list)):
            print(f"Payload:\n{json.dumps(payload, indent=2)}")
            return payload
        else:
            print(f"Payload: {payload}")
            return payload
        print("-----------------------------------")
    except Exception as e:
        print(f"Error in message handler: {e}")

# Set the callback in the plugin instance *before* running the agent
dpsn_plugin.set_message_callback(handle_incoming_message)

def get_agent_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """Update state based on the function results"""
    init_state = {}

    if current_state is None:
        return init_state

    if function_result.info is not None:
        current_state.update(function_result.info)

    return current_state

def get_worker_state(function_result: FunctionResult, current_state: dict) -> dict:
    """Update state based on the function results"""
    init_state = {}

    if current_state is None:
        return init_state

    if function_result.info is not None:
        current_state.update(function_result.info)

    return current_state


subscription_worker = WorkerConfig(
    id="subscription_worker",
    worker_description="Worker specialized in managing DPSN topic subscriptions, unsubscriptions, message handling, and shutdown.",
    get_state_fn=get_worker_state,
    action_space=[
        dpsn_plugin.get_function("subscribe"),
        dpsn_plugin.get_function("unsubscribe"),
        dpsn_plugin.get_function("shutdown")
    ],
)

# Initialize the agent
agent = Agent(
    api_key=os.environ.get("GAME_API_KEY"),
    name="DPSN Market Data Agent",
    agent_goal="Monitor SOLUSDT market data from DPSN and process real-time updates.",
    agent_description=(
        "You are an AI agent specialized in DPSN market data processing"
        "You can subscribe dpsn topic"
        "after 5 minutes unsubscribe the topic"
        "next 5 minutes close the connection"
        "\n\nAvailable topics:"
        "\n- 0xe14768a6d8798e4390ec4cb8a4c991202c2115a5cd7a6c0a7ababcaf93b4d2d4/SOLUSDT/ohlc"
    ),
    get_agent_state_fn=get_agent_state_fn,
    workers=[
        subscription_worker
    ]
)
```

## 📖 API Reference (`DpsnPlugin`)

Key components of the `DpsnPlugin` class:

-   `__init__(dpsn_url: Optional[str] = ..., pvt_key: Optional[str] = ...)`: Constructor. Reads credentials from env vars by default. Raises `ValueError` if credentials are missing.
-   `get_function(fn_name: str) -> Function`: Retrieves the `Function` object (`subscribe`, `unsubscribe`, `shutdown`) for the Game SDK.
-   `set_message_callback(callback: Callable[[Dict[str, Any]], None])`: Registers the function to call when a message is received on a subscribed topic. The callback receives a dictionary (structure depends on the underlying `dpsn-client`).
-   `subscribe(topic: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]`: (Executable Function) Subscribes to a topic. Handles initialization if needed. Returns status, message, and details.
-   `unsubscribe(topic: str) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]`: (Executable Function) Unsubscribes from a topic. Handles initialization if needed. Returns status, message, and details.
-   `shutdown() -> Tuple[FunctionResultStatus, str, Dict[str, Any]]`: (Executable Function) Disconnects the DPSN client gracefully. Returns status, message, and details.
-   `_ensure_initialized()`: (Internal) Manages the lazy initialization of the DPSN client connection. Raises `DpsnInitializationError` on failure.

### Agent-Executable Functions

The plugin exposes the following functions intended to be called via the Game Agent's task execution mechanism:

-   **`subscribe`**:
    -   Description: Subscribe to a DPSN topic.
    -   Args: `topic` (string, required) - The topic to subscribe to.
-   **`unsubscribe`**:
    -   Description: Unsubscribe from a DPSN topic.
    -   Args: `topic` (string, required) - The topic to unsubscribe from.
-   **`shutdown`**:
    -   Description: Shutdown the DPSN client connection.
    -   Args: None.



> In case of any queries regarding DPSN, please reach out to the team on [Telegram](https://t.me/dpsn_dev) 📥.