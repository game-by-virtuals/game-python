from game_sdk.game.custom_types import FunctionResult
from stateofmika_plugin_gamesdk.functions.router import SOMRouter


# Example state function
def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
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


# Create router function
router_fn = SOMRouter()

output = router_fn._execute_query(query="what is the price of bitcoin")
print("-" * 50)
print(output)
print("-" * 50)
