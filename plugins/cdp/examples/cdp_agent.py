from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus
from typing import Dict, Optional, List
import os
import time
import threading
from dotenv import load_dotenv
from cdp_game_sdk.cdp_plugin import CDPPlugin
from cdp import Wallet
# Load environment variables
load_dotenv()

game_api_key = os.environ.get("GAME_API_KEY")
cdp_plugin = CDPPlugin()
cdp_plugin.initialize()

def get_state_fn(function_result: FunctionResult, current_state: dict) -> dict:
    """Simple state management"""
    return {}

def monitor_balance(min_eth: float = 0.1, min_usdc: float = 100.0) -> tuple:
    """
    Monitor wallet balances and maintain minimum levels
    """
    try:
        balances = cdp_plugin.get_wallet_balance()
        print("\nCurrent Balances:")
        print(f"ETH: {balances['eth']}")
        print(f"USDC: {balances['usdc']}")
        
        actions = []
        
        # Check ETH balance
        if balances['eth'] < min_eth:
            print(f"ETH balance below minimum ({min_eth})")
            cdp_plugin.request_testnet_funds("eth")
            actions.append("Requested ETH from faucet")
            
        # Check USDC balance
        if balances['usdc'] < min_usdc:
            print(f"USDC balance below minimum ({min_usdc})")
            cdp_plugin.request_testnet_funds("usdc")
            actions.append("Requested USDC from faucet")
            
        if actions:
            return FunctionResultStatus.DONE, "Replenished low balances", {"actions": actions}
        return FunctionResultStatus.DONE, "Balances adequate", balances
        
    except Exception as e:
        print(f"Error monitoring balances: {e}")
        return FunctionResultStatus.FAILED, f"Error: {str(e)}", {}

def process_transfers() -> tuple:
    """
    Process recent transfers
    """
    try:
        Wallet.create()
        transfers = cdp_plugin.get_transfer_history()
        recent_transfers = transfers[:5]  # Get 5 most recent transfers
        
        print("\nRecent Transfers:")
        for transfer in recent_transfers:
            print(f"ID: {transfer['id']}")
            print(f"Status: {transfer.get('status', 'unknown')}")
            print("---")
            
        return FunctionResultStatus.DONE, "Processed recent transfers", {"transfers": recent_transfers}
    except Exception as e:
        print(f"Error processing transfers: {e}")
        return FunctionResultStatus.FAILED, f"Error: {str(e)}", {}

# Create workers for different tasks
balance_worker = Worker(
    api_key=game_api_key,
    description="Monitor wallet balances",
    instruction="Monitor and maintain minimum balance levels",
    get_state_fn=get_state_fn,
    action_space=[
        Function(
            fn_name="monitor_balance",
            fn_description="Monitor wallet balances",
            args=[],
            executable=monitor_balance
        )
    ]
)

transfer_worker = Worker(
    api_key=game_api_key,
    description="Process transfers",
    instruction="Monitor and process transfers",
    get_state_fn=get_state_fn,
    action_space=[
        Function(
            fn_name="process_transfers",
            fn_description="Process recent transfers",
            args=[],
            executable=process_transfers
        )
    ]
)

def monitor_balances():
    """Monitor balances continuously"""
    while True:
        balance_worker.run("Monitor wallet balances")
        time.sleep(300)  # Check every 5 minutes

def monitor_transfers():
    """Monitor transfers continuously"""
    while True:
        transfer_worker.run("Process recent transfers")
        time.sleep(60)  # Check every minute

def main():
    """
    Main function to start monitoring threads
    """
    print("Starting CDP monitoring agent...")
    
    # Create wallet if not exists
    if not cdp_plugin.wallet:
        wallet = cdp_plugin.create_wallet()
        print(f"Created new wallet: {wallet['address']}")
        
        # Fund wallet
        cdp_plugin.request_testnet_funds("eth")
        cdp_plugin.request_testnet_funds("usdc")
        print("Funded wallet with testnet ETH and USDC")
    
    # Create monitoring threads
    balance_thread = threading.Thread(target=monitor_balances)
    transfer_thread = threading.Thread(target=monitor_transfers)
    
    # Start threads
    balance_thread.start()
    transfer_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitoring...")

if __name__ == "__main__":
    main()
