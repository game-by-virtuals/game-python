"""
Example implementation of a GAME SDK agent with multiple workers.

This example demonstrates how to:
1. Create and configure workers with different capabilities
2. Manage state across workers
3. Define and register custom functions
4. Handle function results and state updates

The example implements a simple environment with objects that workers can interact with
through various actions like taking, throwing, and sitting.
"""

from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus
from typing import Tuple
import os

game_api_key = os.environ.get("GAME_API_KEY")

def get_worker_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    State management function for workers in the example environment.

    This function demonstrates how to maintain and update worker state based on
    function execution results. It shows both static state management and
    dynamic state updates.

    Args:
        function_result (FunctionResult): Result from the previous function execution.
        current_state (dict): Current state of the worker.

    Returns:
        dict: Updated state containing available objects and their properties.

    Note:
        This example uses a fixed state for simplicity, but you can implement
        dynamic state updates based on function_result.info.
    """
    # Dict containing info about the function result as implemented in the executable
    info = function_result.info 

    # Example of fixed state - the first state placed here is the initial state
    init_state = {
        "objects": [
            {"name": "apple", "description": "A red apple", "type": ["item", "food"]},
            {"name": "banana", "description": "A yellow banana", "type": ["item", "food"]},
            {"name": "orange", "description": "A juicy orange", "type": ["item", "food"]},
            {"name": "chair", "description": "A chair", "type": ["sittable"]},
            {"name": "table", "description": "A table", "type": ["sittable"]},
        ]
    }

    if current_state is None:
        # at the first step, initialise the state with just the init state
        new_state = init_state
    else:
        # do something wiht the current state input and the function result info
        new_state = init_state # this is just an example where the state is static

    return new_state

def get_agent_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """
    State management function for the main agent.

    Maintains the high-level state of the agent, which can be different from
    or aggregate the states of individual workers.

    Args:
        function_result (FunctionResult): Result from the previous function execution.
        current_state (dict): Current state of the agent.

    Returns:
        dict: Updated agent state.
    """

    # example of fixed state (function result info is not used to change state) - the first state placed here is the initial state
    init_state = {
        "objects": [
            {"name": "apple", "description": "A red apple", "type": ["item", "food"]},
            {"name": "banana", "description": "A yellow banana", "type": ["item", "food"]},
            {"name": "orange", "description": "A juicy orange", "type": ["item", "food"]},
            {"name": "chair", "description": "A chair", "type": ["sittable"]},
            {"name": "table", "description": "A table", "type": ["sittable"]},
        ]
    }

    if current_state is None:
        # at the first step, initialise the state with just the init state
        new_state = init_state
    else:
        # do something wiht the current state input and the function result info
        new_state = init_state # this is just an example where the state is static

    return new_state


def take_object(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """
    Function to take an object from the environment.

    Args:
        object (str): Name of the object to take.
        **kwargs: Additional arguments that might be passed.

    Returns:
        Tuple[FunctionResultStatus, str, dict]: Status, feedback message, and state info.

    Example:
        status, msg, info = take_object("apple")
    """
    
    if object:
        return FunctionResultStatus.DONE, f"Successfully took the {object}", {}
    return FunctionResultStatus.FAILED, "No object specified", {}


def throw_object(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """
    Function to throw an object.

    Args:
        object (str): Name of the object to throw.
        **kwargs: Additional arguments that might be passed.

    Returns:
        Tuple[FunctionResultStatus, str, dict]: Status, feedback message, and state info.

    Example:
        status, msg, info = throw_object("ball")
    """
    if object:
        return FunctionResultStatus.DONE, f"Successfully threw the {object}", {}
    return FunctionResultStatus.FAILED, "No object specified", {}


def sit_on_object(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """
    Function to sit on an object.

    Args:
        object (str): Name of the object to sit on.
        **kwargs: Additional arguments that might be passed.

    Returns:
        Tuple[FunctionResultStatus, str, dict]: Status, feedback message, and state info.

    Raises:
        ValueError: If the object is not sittable.

    Example:
        status, msg, info = sit_on_object("chair")
    """
    sittable_objects = {"chair", "bench", "stool", "couch", "sofa", "bed"}
    
    if not object:
        return FunctionResultStatus.FAILED, "No object specified", {}
    
    if object.lower() in sittable_objects:
        return FunctionResultStatus.DONE, f"Successfully sat on the {object}", {}
    
    return FunctionResultStatus.FAILED, f"Cannot sit on {object} - not a sittable object", {}


def throw_fruit(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """
    Specialized function to throw fruit objects.

    This function demonstrates type-specific actions in the environment.

    Args:
        object (str): Name of the fruit to throw.
        **kwargs: Additional arguments that might be passed.

    Returns:
        Tuple[FunctionResultStatus, str, dict]: Status, feedback message, and state info.

    Example:
        status, msg, info = throw_fruit("apple")
    """
    fruits = {"apple", "banana", "orange", "pear", "mango", "grape"}
    
    if not object:
        return FunctionResultStatus.FAILED, "No fruit specified", {}
    
    if object.lower() in fruits:
        return FunctionResultStatus.DONE, f"Successfully threw the {object} across the room!", {}
    return FunctionResultStatus.FAILED, f"Cannot throw {object} - not a fruit", {}


def throw_furniture(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    """
    Specialized function to throw furniture objects.

    This function demonstrates type-specific actions in the environment.

    Args:
        object (str): Name of the furniture to throw.
        **kwargs: Additional arguments that might be passed.

    Returns:
        Tuple[FunctionResultStatus, str, dict]: Status, feedback message, and state info.

    Example:
        status, msg, info = throw_furniture("chair")
    """
    furniture = {"chair", "table", "stool", "lamp", "vase", "cushion"}
    
    if not object:
        return FunctionResultStatus.FAILED, "No furniture specified", {}
    
    if object.lower() in furniture:
        return FunctionResultStatus.DONE, f"Powerfully threw the {object} across the room!", {}
    return FunctionResultStatus.FAILED, f"Cannot throw {object} - not a furniture item", {}


# Create functions for each executable with detailed argument specifications
take_object_fn = Function(
    fn_name="take",
    fn_description="Take object",
    args=[Argument(name="object", type="item", description="Object to take")],
    executable=take_object
)

sit_on_object_fn = Function(
    fn_name="sit",
    fn_description="Sit on object",
    args=[Argument(name="object", type="sittable", description="Object to sit on")],
    executable=sit_on_object
)

throw_object_fn = Function(
    fn_name="throw",
    fn_description="Throw any object",
    args=[Argument(name="object", type="item", description="Object to throw")],
    executable=throw_object
)

throw_fruit_fn = Function(
    fn_name="throw_fruit",
    fn_description="Throw fruit only",
    args=[Argument(name="object", type="item", description="Fruit to throw")],
    executable=throw_fruit
)

throw_furniture_fn = Function(
    fn_name="throw_furniture",
    fn_description="Throw furniture only",
    args=[Argument(name="object", type="item", description="Furniture to throw")],
    executable=throw_furniture
)


# Create the specialized workers
fruit_thrower = WorkerConfig(
    id="fruit_thrower",
    worker_description="A worker specialized in throwing fruits ONLY with precision",
    get_state_fn=get_worker_state_fn,
    action_space=[take_object_fn, sit_on_object_fn, throw_fruit_fn]
)

furniture_thrower = WorkerConfig(
    id="furniture_thrower",
    worker_description="A strong worker specialized in throwing furniture",
    get_state_fn=get_worker_state_fn,
    action_space=[take_object_fn, sit_on_object_fn, throw_furniture_fn]
)

# Create agent with both workers
chaos_agent = Agent(
    api_key=game_api_key,
    name="Chaos",
    agent_goal="Conquer the world by causing chaos.",
    agent_description="You are a mischievous master of chaos is very strong but with a very short attention span, and not so much brains",
    get_agent_state_fn=get_agent_state_fn,
    workers=[fruit_thrower, furniture_thrower],
    model_name="Llama-3.1-405B-Instruct"
)

# # interact and instruct the worker to do something
# chaos_agent.get_worker("fruit_thrower").run("make a mess and rest!")

# # compile and run the agent - if you don't compile the agent, the things you added to the agent will not be saved
chaos_agent.compile()
chaos_agent.run()