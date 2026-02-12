"""
Example: Using Spraay as a Worker in an existing GAME agent.

This is the most common integration pattern — you already have a GAME
agent and want to add batch payment capabilities as a new worker.

Prerequisites:
    pip install game-sdk spraay-plugin-gamesdk
"""

import os
from game_sdk.game.agent import WorkerConfig
from spraay_plugin_gamesdk import SpraayPlugin


# ── Quick Setup ─────────────────────────────────────────────────────

spraay = SpraayPlugin(
    private_key=os.environ.get("SPRAAY_PRIVATE_KEY"),
)

# Create a WorkerConfig you can add to any existing GAME agent
spraay_worker = WorkerConfig(
    id="batch_payments",
    worker_description=(
        "Batch payment worker powered by Spraay. Can send ETH or ERC-20 "
        "tokens to up to 200 recipients in a single Base transaction. "
        "Use for airdrops, payroll, bounties, and reward distributions. "
        "Always check balance first, then estimate cost, then execute."
    ),
    action_space=spraay.get_tools(),
    get_state_fn=lambda: {
        "wallet": spraay.wallet_address,
        "network": "Base Mainnet",
        "contract": "0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC",
    },
)

# ── Add to your existing agent ──────────────────────────────────────
#
# from game_sdk.game.agent import Agent
#
# agent = Agent(
#     api_key=os.environ.get("GAME_API_KEY"),
#     name="My Agent",
#     agent_goal="...",
#     agent_description="...",
#     workers=[
#         your_existing_worker,
#         spraay_worker,          # <-- Just add this
#     ],
# )

print("Spraay worker configured!")
print(f"Wallet: {spraay.wallet_address}")
print(f"Available tools: {[f.fn_name for f in spraay.get_tools()]}")
