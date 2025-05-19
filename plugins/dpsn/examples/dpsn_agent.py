import os
import sys
from pathlib import Path
import json
from datetime import datetime
import time
import threading
import signal
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import FunctionResult, FunctionResultStatus, Function, Argument
from dpsn_plugin_gamesdk.dpsn_plugin import DpsnPlugin
load_dotenv()

dpsn_plugin = DpsnPlugin(
    dpsn_url=os.getenv("DPSN_URL"),
    pvt_key=os.getenv("PVT_KEY")
)


# Global message counter and timestamp
message_count = 0
start_time = None
collected_messages = []
task_completed = False  # Flag to track if the main task has been completed

# Update message handler to track count and time
def handle_incoming_message(message_data: dict):
    """Callback function to process messages received via the plugin."""
    global message_count, start_time, collected_messages
    
    # Don't process messages if task is already completed
    if task_completed:
        return "Task already completed"
    
    # Initialize start time on first message
    if start_time is None:
        start_time = time.time()
    
    message_count += 1
    collected_messages.append(message_data)
    
    topic = message_data.get('topic', 'N/A')
    payload = message_data.get('payload', '{}')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\n--- Message Received ({timestamp}) ---")
    print(f"Topic: {topic}")
    print(f"Message count: {message_count}")
    print(f"Time elapsed: {time.time() - start_time:.1f} seconds")
    
    # Pretty print payload
    if isinstance(payload, (dict, list)):
        print(f"Payload:\n{json.dumps(payload, indent=2)}")
        return json.dumps(payload)
    else:
        print(f"Payload: {payload}")
        return str(payload)

# Add a new function for the agent to check if collection is complete
def check_collection_status() -> tuple[FunctionResultStatus, str, dict]:
    """Check if we have collected enough data (2 minutes or 3+ messages)"""
    global message_count, start_time, collected_messages
    
    elapsed = 0
    if start_time:
        elapsed = time.time() - start_time
    
    # Check conditions
    time_condition = elapsed >= 120  # 2 minutes
    count_condition = message_count >= 3
    
    if time_condition or count_condition:
        reason = "time limit reached" if time_condition else "message count reached"
        summary = {
            "messages_received": message_count,
            "time_elapsed_seconds": elapsed,
            "collection_complete": True,
            "reason": reason,
            "sample_messages": collected_messages[:3]  # First 3 messages as samples
        }
        return (FunctionResultStatus.DONE, f"Data collection complete: {reason}", summary)
    else:
        summary = {
            "messages_received": message_count,
            "time_elapsed_seconds": elapsed,
            "collection_complete": False,
            "remaining_time": 120 - elapsed,
            "remaining_messages": max(0, 3 - message_count)
        }
        return (FunctionResultStatus.DONE, "Still collecting data...", summary)

# Function to mark a task completed after dpsn shutdown
def mark_complete_after_shutdown() -> tuple[FunctionResultStatus, str, dict]:
    """Mark the task as complete after DPSN client shutdown"""
    global task_completed
    
    # Only allow this to be called if DPSN was already shut down
    if task_completed:
        return (FunctionResultStatus.DONE, "Task already marked as complete.", {"status": "already_completed"})
    
    # Explain what's happening
    print("\n=== FINALIZING TASK ===")
    print("1. DPSN Client has been shut down")
    print("2. Marking task as complete")
    print("3. Program will exit shortly")
    task_completed = True
    
    # Schedule a delayed exit to allow time for the agent to report completion
    def exit_program():
        print("\n=== TASK COMPLETE ===")
        print("Exiting program as all tasks are complete...")
        os._exit(0)  # Force exit the program
    
    # Schedule exit after 5 seconds
    timer = threading.Timer(5.0, exit_program)
    timer.daemon = True
    timer.start()
    
    return (FunctionResultStatus.DONE, "Task complete! Agent is now finished.", {"status": "success"})

# Create a function objects for the functions
check_status_function = Function(
    fn_name="check_collection_status",
    fn_description="Check if enough data has been collected (2 minutes or 3+ messages)",
    args=[],
    hint="Use this to check if it's time to unsubscribe (returns collection status)",
    executable=check_collection_status
)

complete_task_function = Function(
    fn_name="mark_task_complete",
    fn_description="Mark the agent task as complete and exit the program",
    args=[],
    hint="Use this as the VERY LAST step after unsubscribing and shutting down DPSN",
    executable=mark_complete_after_shutdown
)

# Set the callback in the plugin instance *before* running the agent
dpsn_plugin.set_message_callback(handle_incoming_message)
# --- End Message Handler Setup ---

def get_agent_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """Update state based on the function results"""
    init_state = {}

    if current_state is None:
        current_state = init_state  # Initialize if None

    # Check if function_result is None (initial call)
    if function_result is None:
        return current_state # Return current (likely initial) state

    if function_result.info is not None:
        current_state.update(function_result.info)

    # Check if we have completion info
    if function_result.info and 'status' in function_result.info and function_result.info['status'] == 'success':
        current_state['task_completed'] = True
        # If we're marking task as complete, set state to indicate we're done
        print("Agent state updated: Task marked as complete.")
    
    # Add a delay if we just checked status and collection is NOT complete
    # Check if the 'collection_complete' key exists in the info dict 
    # to infer that check_collection_status was likely the last function run.
    if function_result.info and \
       "collection_complete" in function_result.info and \
       not function_result.info.get("collection_complete", True):
        
        wait_time = 5 # Wait for 5 seconds before next check
        print(f"Collection not complete. Waiting {wait_time} seconds before next action...")
        time.sleep(wait_time)

    return current_state

def get_worker_state(function_result: FunctionResult, current_state: dict) -> dict:
    """Update state based on the function results"""
    init_state = {}

    if current_state is None:
        return init_state

    if function_result.info is not None:
        current_state.update(function_result.info)

    return current_state

subscription_worker = WorkerConfig(
    id="subscription_worker",
    worker_description="Worker specialized in managing DPSN topic subscriptions, unsubscriptions, message handling, and shutdown.",
    get_state_fn=get_worker_state,
    action_space=[
        dpsn_plugin.get_function("subscribe"),
        dpsn_plugin.get_function("unsubscribe"),
        dpsn_plugin.get_function("shutdown"),
        check_status_function,
        complete_task_function  # Add the task completion function
    ],
)


# Initialize the agent
agent = Agent(
    api_key=os.environ.get("GAME_API_KEY"),
    name="DPSN Market Data Agent",
    agent_goal="Monitor SOLUSDT market data from DPSN, process messages for 2 minutes, then clean up and exit.",
    agent_description=(
        "You are an AI agent specialized in DPSN market data processing. Follow these steps in order:\n\n"
        
        "1. IMMEDIATELY subscribe to this DPSN topic: 0xe14768a6d8798e4390ec4cb8a4c991202c2115a5cd7a6c0a7ababcaf93b4d2d4/SOLUSDT/ohlc\n"
        
        "2. Once subscribed, inform the user that you are listening for market data updates.\n"
        
        "3. When you receive messages on this topic:\n"
        "   - Report that you received a message\n"
        
        "4. After subscribing, periodically use the check_collection_status function to check if:\n"
        "   - 2 minutes have passed, OR\n"
        "   - At least 3 messages have been received\n"
        
        "5. Only when check_collection_status indicates collection is complete:\n"
        "   - Unsubscribe from the topic using the unsubscribe function\n"
        "   - Shut down the DPSN client connection using the shutdown function\n"
        
        "6. FINAL STEP: After shutting down the DPSN connection, call the mark_task_complete function.\n"
        "   This will finish your task and automatically exit the program after 5 seconds.\n"
        "   This must be the VERY LAST function you call.\n"

        "IMPORTANT: The program will exit automatically after you mark the task complete.\n"
        
        "Available functions:\n"
        "- subscribe: Subscribe to a DPSN topic to receive data\n"
        "- unsubscribe: Unsubscribe from a DPSN topic\n"
        "- shutdown: Close the DPSN client connection\n"
        "- check_collection_status: Check if collection is complete\n"
        "- mark_task_complete: Mark the agent's task as complete and exit the program\n\n"
        
        "Available topic:\n"
        "- 0xe14768a6d8798e4390ec4cb8a4c991202c2115a5cd7a6c0a7ababcaf93b4d2d4/SOLUSDT/ohlc"
    ),
    get_agent_state_fn=get_agent_state_fn,
    workers=[
        subscription_worker
    ]
)

try:
    print("\n=== DPSN AGENT STARTING ===")
    print("This agent will:")
    print("1. Subscribe to the SOLUSDT/ohlc topic")
    print("2. Collect messages for 2 minutes or at least 3 messages")
    print("3. Unsubscribe and clean up")
    print("4. Exit automatically\n")
    
    agent.compile()
    agent.run() 
except Exception as e:
    print(f"Error running agent:{e}")
    import traceback
    traceback.print_exc()
