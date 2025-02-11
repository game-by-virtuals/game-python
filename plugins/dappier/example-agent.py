# agent.py
import os
from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import FunctionResult
from dappier_plugin import DappierPlugin

def get_agent_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on the function results
    """
    init_state = {}

    if current_state is None:
        return init_state

    if function_result.info is not None:
        current_state.update(function_result.info)

    return current_state

def get_worker_state(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on the function results
    """
    init_state = {}

    if current_state is None:
        return init_state

    if function_result.info is not None:
        current_state.update(function_result.info)

    return current_state

# Initialize the Dappier plugin
dappier_plugin = DappierPlugin(
    api_key=os.environ.get("DAPPIER_API_KEY"),
)

# Create worker configurations
real_time_search_worker = WorkerConfig(
    id="real_time_search_worker",
    worker_description="Worker specialized in performing real-time data searches using Dappier",
    get_state_fn=get_worker_state,
    action_space=[
        dappier_plugin.get_function("search_real_time_data"),
    ],
)

recommendations_worker = WorkerConfig(
    id="recommendations_worker",
    worker_description="Worker specialized in getting AI-powered recommendations from Dappier",
    get_state_fn=get_worker_state,
    action_space=[
        dappier_plugin.get_function("get_ai_recommendations"),
    ]
)

# Initialize the agent
agent = Agent(
    api_key=os.environ.get("GAME_API_KEY"),
    name="Dappier Agent",
    agent_goal="Help users fetch real-time data and get AI-powered recommendations using Dappier.",
    agent_description=(
        "You are an AI agent specialized in using Dappier services. "
        "You can perform real-time data searches and get AI-powered recommendations. "
        "You understand how to use different AI models and data models from the Dappier marketplace."
    ),
    get_agent_state_fn=get_agent_state_fn,
    workers=[
        real_time_search_worker,
        recommendations_worker,
    ]
)

agent.compile()
agent.run()