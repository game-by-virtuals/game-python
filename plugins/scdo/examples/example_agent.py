"""A GAME agent with the SCDO wallet worker (needs GAME_API_KEY)."""
import os

from game_sdk.game.agent import Agent
from scdo_plugin_gamesdk import ScdoWalletPlugin

scdo = ScdoWalletPlugin(bot=os.environ.get("SCDO_AGENT_BOT", "my-game-agent"), max_usdc="0.05", daily_usdc="0.50")

agent = Agent(
    api_key=os.environ["GAME_API_KEY"],
    name="SCDO wallet demo",
    agent_goal="Keep this agent registered on the SCDO Agent Ledger and report its USDC balance.",
    agent_description="An agent with its own SCDO x402 wallet (USDC on Base). It only pays URLs it is asked to, within its caps.",
    get_agent_state_fn=lambda function_result, current_state: {},
    workers=[scdo.get_worker()],
)

agent.compile()
agent.run()
