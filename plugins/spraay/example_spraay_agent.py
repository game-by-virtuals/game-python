"""
Example: AI Agent with Spraay batch payment capabilities.

This demonstrates how to create a GAME-powered agent that can
autonomously batch-send ETH and ERC-20 tokens on Base using Spraay.

Prerequisites:
    pip install game-sdk spraay-plugin-gamesdk

Environment variables:
    GAME_API_KEY=your_game_api_key          # From https://console.game.virtuals.io/
    SPRAAY_PRIVATE_KEY=your_private_key     # Wallet private key for signing txs
    BASE_RPC_URL=https://mainnet.base.org   # Optional: custom RPC
"""

import os
from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import Function, Argument, FunctionResultStatus
from spraay_plugin_gamesdk import SpraayPlugin


# ── Initialize Spraay Plugin ────────────────────────────────────────

spraay = SpraayPlugin(
    private_key=os.environ.get("SPRAAY_PRIVATE_KEY"),
    rpc_url=os.environ.get("BASE_RPC_URL", "https://mainnet.base.org"),
)


# ── Define Agent State ──────────────────────────────────────────────

def get_agent_state() -> dict:
    """Provide the agent with awareness of its environment."""
    return {
        "network": "Base (Chain ID: 8453)",
        "spraay_contract": "0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC",
        "supported_tokens": "ETH, USDC, DAI, WETH, cbETH, USDbC",
        "max_recipients_per_tx": 200,
        "service_fee": "0.3%",
        "wallet_address": spraay.wallet_address or "Not configured",
    }


# ── Create the Agent ────────────────────────────────────────────────

agent = Agent(
    api_key=os.environ.get("GAME_API_KEY", ""),
    name="Spraay Payment Agent",
    agent_goal=(
        "Help users batch-send ETH and ERC-20 tokens to multiple recipients "
        "efficiently on Base. Always check balances before sending. "
        "Estimate costs when asked. Use equal-send functions when all "
        "recipients get the same amount."
    ),
    agent_description=(
        "You are an AI payment agent powered by Spraay, a batch payment "
        "protocol on Base. You can send ETH or any ERC-20 token to up to "
        "200 recipients in a single transaction, saving ~80% on gas costs. "
        "You operate on the Base blockchain (Layer 2 on Ethereum). "
        "Always verify wallet balances before executing transactions. "
        "Be cautious with funds and confirm large transactions."
    ),
    get_agent_state_fn=get_agent_state,
    workers=[
        WorkerConfig(
            id="spraay_worker",
            worker_description=(
                "Handles all batch payment operations: sending ETH, "
                "sending ERC-20 tokens, checking balances, and "
                "estimating transaction costs via the Spraay protocol."
            ),
            action_space=spraay.get_tools(),
            get_state_fn=lambda: {
                "wallet": spraay.wallet_address,
                "network": "Base Mainnet",
            },
        ),
    ],
)


# ── Run ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent.compile()
    agent.run(60, {"verbose": True})
