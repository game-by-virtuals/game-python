from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import (
    Function, 
    Argument, 
    FunctionResult, 
    FunctionResultStatus
)
from typing import Dict
import os
from dotenv import load_dotenv
from cdp_game_sdk.cdp_plugin import CDPPlugin

class CDPWorker:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.game_api_key = os.environ.get("GAME_API_KEY")
        self.cdp_plugin = CDPPlugin()
        self.cdp_plugin.initialize()
        self.worker = self._create_worker()

    def _get_state(self, function_result: FunctionResult, current_state: dict) -> dict:
        """Simple state management"""
        return {}

    def create_and_fund_wallet(self) -> tuple:
        """
        Create a new wallet and fund it with testnet ETH and USDC
        """
        try:
            # Create wallet
            wallet = self.cdp_plugin.create_wallet()
            print(f"Created wallet: {wallet['address']}")
            
            # Request testnet funds
            eth_result = self.cdp_plugin.request_testnet_funds("eth")
            usdc_result = self.cdp_plugin.request_testnet_funds("usdc")
            
            print("Funded wallet with testnet ETH and USDC")
            
            return FunctionResultStatus.DONE, "Wallet created and funded", {
                "wallet": wallet,
                "eth_tx": eth_result,
                "usdc_tx": usdc_result
            }
        except Exception as e:
            print(f"Error creating/funding wallet: {e}")
            return FunctionResultStatus.FAILED, f"Error: {str(e)}", {}

    def transfer_usdc(self, to_address: str, amount: float) -> tuple:
        """
        Transfer USDC to an address
        """
        try:
            result = self.cdp_plugin.transfer(
                amount=amount,
                currency="usdc",
                to_address=to_address,
                gasless=True
            )
            print(f"Transferred {amount} USDC to {to_address}")
            return FunctionResultStatus.DONE, "Transfer successful", result
        except Exception as e:
            print(f"Error transferring USDC: {e}")
            return FunctionResultStatus.FAILED, f"Error: {str(e)}", {}

    def trade_eth_for_usdc(self, amount: float) -> tuple:
        """
        Trade ETH for USDC
        """
        try:
            result = self.cdp_plugin.trade(
                amount=amount,
                from_currency="eth",
                to_currency="usdc"
            )
            print(f"Traded {amount} ETH for USDC")
            return FunctionResultStatus.DONE, "Trade successful", result
        except Exception as e:
            print(f"Error trading ETH for USDC: {e}")
            return FunctionResultStatus.FAILED, f"Error: {str(e)}", {}

    def _create_worker(self) -> Worker:
        """Create worker with CDP capabilities"""
        return Worker(
            api_key=self.game_api_key,
            description="Worker for CDP operations",
            instruction="Perform CDP operations like transfers and trades",
            get_state_fn=self._get_state,
            action_space=[
                Function(
                    fn_name="create_and_fund_wallet",
                    fn_description="Create a new wallet and fund it with testnet assets",
                    args=[],
                    executable=self.create_and_fund_wallet
                ),
                Function(
                    fn_name="transfer_usdc",
                    fn_description="Transfer USDC to an address",
                    args=[
                        Argument(
                            name="to_address",
                            type="string",
                            description="Recipient address"
                        ),
                        Argument(
                            name="amount",
                            type="float",
                            description="Amount of USDC to transfer"
                        )
                    ],
                    executable=self.transfer_usdc
                ),
                Function(
                    fn_name="trade_eth_for_usdc",
                    fn_description="Trade ETH for USDC",
                    args=[
                        Argument(
                            name="amount",
                            type="float",
                            description="Amount of ETH to trade"
                        )
                    ],
                    executable=self.trade_eth_for_usdc
                )
            ]
        )

    def run(self, function_name: str, **kwargs):
        """Run the worker with specified function"""
        self.worker.run(f"Execute {function_name}", **kwargs)

def main():
    # Example usage
    worker = CDPWorker()
    
    # Create and fund a wallet
    worker.run("create_and_fund_wallet")
    
    # Make a transfer
    worker.run("transfer_usdc", to_address="0x123...", amount=10.0)
    
    # Trade ETH for USDC
    worker.run("trade_eth_for_usdc", amount=0.1)

if __name__ == "__main__":
    main() 