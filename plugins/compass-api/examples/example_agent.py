"""Adapted from compass.virtuals_sdk.simple_agent."""
from game_sdk.game.agent import Agent, WorkerConfig

from compass.api_client import Chain
from compass.virtuals_sdk.api_wrapper import (
    AaveV3,
    AerodromeBasic,
    AerodromeSlipstream,
    Others,
    UniswapV3,
)
from compass.virtuals_sdk.config import api_key
from compass.virtuals_sdk.shared_defaults import get_state_fn

available_chains = [i.value for i in Chain]
worker_instruction = "Interact with your assigned defi protocol."

compass_agent = Agent(
    api_key=api_key,
    name="A defi agent that can operate on multiple defi exchanges",
    agent_goal=f"Find oppotunities to make money by identifying price differences on different protocols. Then create transactions that could be used to perform the trades that make the money (just create them, do not send them). Set all user and sender addresses to 0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43 and chain to ethereum.",
    agent_description="defi agent",
    get_agent_state_fn=get_state_fn,
    workers=[
        WorkerConfig(cls.id, cls.worker_description+". Set all user and sender addresses to 0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43 and chain to ethereum.", cls.get_state_fn, cls.action_space)
        # wallet excluded - include it if you want to start moving funds
        for cls in [AerodromeBasic, AerodromeSlipstream, AaveV3, Others, UniswapV3]
    ],
)

if __name__ == "__main__":
    compass_agent.compile()
    compass_agent.run()
 