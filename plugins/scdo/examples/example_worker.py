"""Run one SCDO wallet worker on its own (needs GAME_API_KEY; Linux for the auto-downloaded scdo-agent CLI)."""
import os

from game_sdk.game.worker import Worker
from scdo_plugin_gamesdk import ScdoWalletPlugin

scdo = ScdoWalletPlugin(bot=os.environ.get("SCDO_AGENT_BOT", "my-game-agent"))

worker = Worker(
    api_key=os.environ["GAME_API_KEY"],
    description="Holds this agent's own SCDO x402 USDC wallet on Base.",
    instruction="Register the agent, then report its wallet address and balance.",
    get_state_fn=scdo.get_state,
    action_space=scdo.get_functions(),
)

worker.run("Register this agent with SCDO and show its wallet balance.")
