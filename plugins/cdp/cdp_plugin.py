import asyncio
import json
from typing import Dict, List, Optional, Tuple
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from cdp import *
import logging

logger = logging.getLogger(__name__)

class CdpPlugin:
    """
    Coinbase Developer Platform plugin.

    This plugin is used to interact with the Coinbase Developer Platform.
    You'll need to have a Coinbase Developer Platform account to use this plugin.
    If you don't have one, you can sign up at https://developer.coinbase.com/

    Create your API key and private key in the Coinbase Developer Platform dashboard:
    https://portal.cdp.coinbase.com/access/api.

    Example:
        from cdp.cdp_plugin import CdpPlugin

        client = CdpPlugin(
            cdp_api_key_name=os.environ.get("CDP_API_KEY_NAME"),
            cdp_api_key_private_key=os.environ.get("CDP_API_KEY_PRIVATE_KEY"),
        )

        get_balances = client.get_function("get_balances")
        result_status, msg, info = get_balances.executable()

        OR

        result_status, msg, info = client.get_balances()
    """

    def __init__(
        self,
        cdp_api_key_name: Optional[str] = None,
        cdp_api_key_private_key: Optional[str] = None,
        cdp_credentials_path: Optional[str] = None,
    ):
        """
        Initialize the CDP client.

        Args:
            cdp_api_key_name (str): CDP API key name
            cdp_api_key_private_key (str): CDP API key private key
            cdp_credentials_path (str): Path to the CDP credentials file
        """
        if cdp_credentials_path:
            Cdp.configure_from_json(cdp_credentials_path)
            logger.info(f"CDP SDK has been successfully configured with CDP API key.")
        elif cdp_api_key_name and cdp_api_key_private_key:
            Cdp.configure(cdp_api_key_name, cdp_api_key_private_key)
            logger.info(f"CDP SDK has been successfully configured with CDP API key.")
        else:
            raise ValueError("Either cdp_credentials_path or cdp_api_key_name and cdp_api_key_private_key must be provided.")

        # TODO: Add configuration from json file
        # Cdp.configure_from_json("~/Downloads/cdp_api_key.json")

        self.wallet = None

        # Available client functions
        self._functions: Dict[str, Function] = {
            "create_wallet": Function(
                fn_name="create_wallet",
                fn_description="Create a wallet with one address by default.",
                args=[],
                hint="This function creates a wallet with one address by default.",
                executable=self.create_wallet,
            ),
            "add_funds_from_faucet": Function(
                fn_name="add_funds_from_faucet",
                fn_description="Add funds to the wallet from the faucet.",
                args=[],
                hint="This function add funds to the wallet from the faucet.",
                executable=self.add_funds_from_faucet,
            ),
            "get_balances": Function(
                fn_name="get_balances",
                fn_description="Get the balances of the wallet.",
                args=[],
                hint="This function is used to get the balances of the wallet.",
                executable=self.get_balances,
            ),
        }

    @property
    def available_functions(self) -> List[str]:
        """Get list of available function names."""
        return list(self._functions.keys())

    def get_function(self, fn_name: str) -> Function:
        """
        Get a specific function by name.

        Args:
            fn_name: Name of the function to retrieve

        Raises:
            ValueError: If function name is not found

        Returns:
            Function object
        """
        if fn_name not in self._functions:
            raise ValueError(
                f"Function '{fn_name}' not found. Available functions: {', '.join(self.available_functions)}"
            )
        return self._functions[fn_name]

    
    def create_wallet(self) -> Tuple[FunctionResultStatus, str, dict]:
        """
        Create a wallet with one address by default.
        """
        try:
            self.wallet = Wallet.create()
            logger.info(f"Wallet created: {self.wallet}")

            address = self.wallet.default_address
            logger.info(f"Default address for the wallet: {self.address}")
        except Exception as e:
            logger.error(f"Wallet error: {str(e)}")
            return FunctionResultStatus.FAILED, f"Failed to create wallet: {str(e)}", {}
            
        return FunctionResultStatus.DONE, f"Successfully created a wallet with one address by default.", {'address': self.address}


    def get_balances(self) -> Tuple[FunctionResultStatus, str, dict]:
        """
        Get the balance of a given symbol.
        """
        try:
            balances = self.wallet.balances()
            logger.info(f"Balances of the wallet: {balances}")
        except Exception as e:
            logger.error(f"Balances error: {str(e)}")
            return FunctionResultStatus.FAILED, f"Failed to get the balances of the wallet: {str(e)}", {}

        return FunctionResultStatus.DONE, f"Successfully checked the balances of the wallet", {'balances': balances}


    def add_funds_from_faucet(self) -> Tuple[FunctionResultStatus, str, dict]:
        """
        Add funds to the wallet from the faucet.
        """
        try:
            faucet_tx = self.wallet.faucet()
            faucet_tx.wait()

            logger.info(f"Faucet transaction successfully completed: {faucet_tx}")
        except Exception as e:
            logger.error(f"Faucet transaction error: {str(e)}")
            return FunctionResultStatus.FAILED, f"Failed to add funds to the wallet from the faucet: {str(e)}", {}

        return FunctionResultStatus.DONE, f"Successfully added funds to the wallet from the faucet.", {'tx': faucet_tx}
