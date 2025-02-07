import os
from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import FunctionResult

from stateofmika_plugin_gamesdk.functions.router import SOMRouter


def get_agent_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on router responses
    """
    init_state = {"previous_queries": [], "previous_routes": []}

    if current_state is None:
        return init_state

    # Update state with results
    if function_result and function_result.info:
        current_state["previous_queries"].append(function_result.info.get("query", ""))
        current_state["previous_routes"].append(function_result.info.get("route", {}))

    return current_state


def get_worker_state(function_result: FunctionResult, current_state: dict) -> dict:
    """
    Update state based on router responses
    """
    init_state = {"previous_queries": [], "previous_routes": []}

    if current_state is None:
        return init_state

    # Update state with results
    if function_result and function_result.info:
        current_state["previous_queries"].append(function_result.info.get("query", ""))
        current_state["previous_routes"].append(function_result.info.get("route", {}))

    return current_state


mika_router = SOMRouter()

price_inference_worker = WorkerConfig(
    id="som_router",
    worker_description="Worker specialized in routing natural language query to appropriate tools and process responses",
    get_state_fn=get_worker_state,
    action_space=[
        mika_router.get_function(),
    ],
)

# Initialize the agent
agent = Agent(
    api_key=os.environ.get("GAME_API_KEY"),
    name="Mika Agent",
    agent_goal="Help user get the latest bitcoin price",
    agent_description=(
        "You are an AI agent specialized in routing natural language query to appropriate tools and process responses"
    ),
    get_agent_state_fn=get_agent_state_fn,
    workers=[
        price_inference_worker,
    ],
)

agent.compile()
agent.run()
