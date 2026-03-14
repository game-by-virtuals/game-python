"""
Example: Virtuals GAME worker with Junct crypto tools.
"""
import os
from game_sdk.game.worker import Worker
from junct_game_sdk.junct_plugin import JunctPlugin


def get_state_fn(worker, function_result):
    return {"status": "ready"}


def main():
    plugin = JunctPlugin()

    worker = Worker(
        api_key=os.environ.get("GAME_API_KEY", ""),
        description="Crypto data agent with access to 20+ DeFi protocols via Junct",
        instruction="You have access to crypto data tools. Use list_junct_servers to see available servers, list_junct_tools to discover tools, and call_junct_tool to fetch data.",
        get_state_fn=get_state_fn,
        action_space=[
            plugin.get_function("list_junct_servers"),
            plugin.get_function("list_junct_tools"),
            plugin.get_function("call_junct_tool"),
        ],
    )

    worker.run("What is the current ETH price on Chainlink?")


if __name__ == "__main__":
    main()
