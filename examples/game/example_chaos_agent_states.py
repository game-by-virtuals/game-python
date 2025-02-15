from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus
from typing import Tuple
import os
import time

game_api_key = os.environ.get("GAME_API_KEY")

def fruit_thrower_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    init_state = {
        "objects": [
            {"name": "apple", "description": "A red apple", "type": ["item", "food"], "destruction_level": 0},
            {"name": "banana", "description": "A yellow banana", "type": ["item", "food"], "destruction_level": 0},
            {"name": "orange", "description": "A juicy orange", "type": ["item", "food"], "destruction_level": 0}
        ]
    }
    if current_state is None:
        return init_state
    if function_result.info is not None:
        # Update state with the function result info
        object = function_result.info.get("object", None)
        action = function_result.info.get("action", None)
        if action == "throw":
            for obj in current_state["objects"]:
                if obj["name"] == object:
                    obj["destruction_level"] += 1
                    break
    return current_state

def furniture_thrower_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    init_state = {
        "objects": [
            {"name": "chair", "description": "A chair", "type": ["sittable"], "destruction_level": 0},
            {"name": "table", "description": "A table", "type": ["sittable"], "destruction_level": 0}
        ]
    }
    if current_state is None:
        return init_state
    if function_result.info is not None:
        # Update state with the function result info
        object = function_result.info.get("object", None)
        action = function_result.info.get("action", None)
        if action == "throw":
            for obj in current_state["objects"]:
                if obj["name"] == object:
                    obj["destruction_level"] -= 1
                    break
    return current_state

def static_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    return {}

def get_agent_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    init_state = {
        "agent_metrics": {
            "energy_level": 5,
            "total_destruction_level": 0,
            "number_of_objects_held": 0
        },
        "objects": [
            {"name": "apple", "description": "A red apple", "type": ["item", "food"], "destruction_level": 0},
            {"name": "banana", "description": "A yellow banana", "type": ["item", "food"], "destruction_level": 0},
            {"name": "orange", "description": "A juicy orange", "type": ["item", "food"], "destruction_level": 0},
            {"name": "chair", "description": "A chair", "type": ["sittable"], "destruction_level": 0},
            {"name": "table", "description": "A table", "type": ["sittable"], "destruction_level": 0}
        ],
        "agent_actions_log": []
    }
    if current_state is None:
        return init_state
    if function_result:
        if function_result.info:
            # Update state with the function result info
            action = function_result.info.get("action", None)
            if action == "throw":
                current_state["agent_metrics"]["energy_level"] -= 2
                current_state["agent_metrics"]["total_destruction_level"] += 1
                current_state["agent_metrics"]["number_of_objects_held"] -= 1
            elif action == "take":
                current_state["agent_metrics"]["energy_level"] -= 1
                current_state["agent_metrics"]["number_of_objects_held"] += 1
            elif action == "sit":
                current_state["agent_metrics"]["energy_level"] += 1
        if function_result.feedback_message is not None:
            current_state["agent_actions_log"].append(function_result.feedback_message)
            print(f"FEEDBACK : {function_result.feedback_message}")
            print(current_state)
    return current_state


def take_object(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    if object:
        return FunctionResultStatus.DONE, f"Successfully took the {object}", {"object": object, "action": "take"}
    return FunctionResultStatus.FAILED, "No object specified", {}


def throw_object(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    if object:
        return FunctionResultStatus.DONE, f"Successfully threw the {object}", {"object": object, "action": "throw"}
    return FunctionResultStatus.FAILED, "No object specified", {}


def sit_on_object(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    sittable_objects = {"chair", "bench", "stool", "couch", "sofa", "bed"}
    if not object:
        return FunctionResultStatus.FAILED, "No object specified", {}
    if object.lower() in sittable_objects:
        return FunctionResultStatus.DONE, f"Successfully sat on the {object}", {"object": object, "action": "sit"}
    return FunctionResultStatus.FAILED, f"Cannot sit on {object} - not a sittable object", {}


def throw_fruit(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    fruits = {"apple", "banana", "orange", "pear", "mango", "grape"}
    if not object:
        return FunctionResultStatus.FAILED, "No fruit specified", {}
    if object.lower() in fruits:
        return FunctionResultStatus.DONE, f"Successfully threw the {object} across the room!", {"object": object, "action": "throw"}
    return FunctionResultStatus.FAILED, f"Cannot throw {object} - not a fruit", {}


def throw_furniture(object: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
    furniture = {"chair", "table", "stool", "lamp", "vase", "cushion"}
    if not object:
        return FunctionResultStatus.FAILED, "No furniture specified", {}
    if object.lower() in furniture:
        return FunctionResultStatus.DONE, f"Powerfully threw the {object} across the room!", {"object": object, "action": "throw"}
    return FunctionResultStatus.FAILED, f"Cannot throw {object} - not a furniture item", {}

def wait() -> Tuple[FunctionResultStatus, str, dict]:
    time.sleep(60)
    return FunctionResultStatus.DONE, f"Waiting for further instruction because there is nothing to do", {}


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
    fn_description="Throw any object. This is only possible when the worker has taken the object.",
    args=[Argument(name="object", type="item", description="Object to throw")],
    executable=throw_object
)

throw_fruit_fn = Function(
    fn_name="throw_fruit",
    fn_description="Throw fruit only. This is only possible when the worker has taken the fruit.",
    args=[Argument(name="object", type="item", description="A type of fruit to throw")],
    executable=throw_fruit
)

throw_furniture_fn = Function(
    fn_name="throw_furniture",
    fn_description="Throw furniture only",
    args=[Argument(name="object", type="item", description="A type of furniture to throw")],
    executable=throw_furniture
)

wait_fn = Function(
    fn_name="wait",
    fn_description="Wait for further instructions because there is nothing else to do",
    args=[],
    executable=wait
)


# Create the specialized workers
fruit_handler = WorkerConfig(
    id="fruit_handler",
    worker_description="A worker specialized in throwing fruits ONLY with precision",
    get_state_fn=fruit_thrower_state_fn,
    action_space=[take_object_fn, sit_on_object_fn, throw_fruit_fn]
)

furniture_handler = WorkerConfig(
    id="furniture_handler",
    worker_description="A strong worker specialized in throwing furniture",
    get_state_fn=furniture_thrower_state_fn,
    action_space=[take_object_fn, sit_on_object_fn, throw_furniture_fn]
)

wait_handler = WorkerConfig(
    id="wait_handler",
    worker_description="A worker specialized in waiting for more instructions",
    get_state_fn=static_state_fn,
    action_space=[wait_fn]
)

# Create agent with both workers
chaos_agent = Agent(
    api_key=game_api_key,
    name="Chaos",
    agent_goal="""Conquer the world by causing as much chaos as possible.  
    Perform the following in order of priority, with 1 being the highest, followed by 2, 3, 4 etc.
    1. If your energy_level is 1 or lower, you MUST wait for instructions at the wait_handler location AND MUST NOT throw anything else. 
    2. If you are holding 2 objects, you MUST throw one IMMEDIATELY."
    """,
    agent_description="You are a mischievous master of chaos and you are very strong. However, you cannot do anything except wait when you have no energy.",
    get_agent_state_fn=get_agent_state_fn,
    workers=[fruit_handler, furniture_handler, wait_handler]
)

# # compile and run the agent - if you don't compile the agent, the things you added to the agent will not be saved
chaos_agent.compile()
chaos_agent.run()