from typing import Dict, Any, Optional, List
import os
from cdp import *
from cdp.client.models.webhook import WebhookEventType, WebhookEventFilter

    
class CDPPlugin:
    """
    Coinbase Developer Platform Plugin for interacting with CDP
    """
    
    def __init__(self) -> None:
        """Initialize the CDP plugin"""
        self.id: str = "cdp_plugin"
        self.name: str = "CDP Plugin"
        self.api_key_name = os.environ.get("CDP_API_KEY_NAME")
        self.api_key_private_key = os.environ.get("CDP_API_KEY_PRIVATE_KEY")
        self.network = "base-sepolia"  # Default to testnet
        self.wallet = None
        
    def initialize(self, use_server_signer: bool = False):
        """Initialize the plugin"""
        if not self.api_key_name:
            raise ValueError("CDP_API_KEY_NAME environment variable is required")
        if not self.api_key_private_key:
            raise ValueError("CDP_API_KEY_PRIVATE_KEY environment variable is required")
        
        # Configure CDP
        Cdp.configure(self.api_key_name, self.api_key_private_key)
        if use_server_signer:
            Cdp.use_server_signer = True

    def create_wallet(self) -> Dict[str, Any]:
        """Create a new wallet"""
        self.wallet = Wallet.create(self.network)
        return {
            "wallet_id": self.wallet.id,
            "address": self.wallet.default_address.address_id
        }

    def import_wallet(self, wallet_id: str, seed_file: str = None) -> None:
        """Import an existing wallet"""
        self.wallet = Wallet.fetch(wallet_id)
        if seed_file:
            self.wallet.load_seed(seed_file)

    def get_wallet_balance(self) -> Dict[str, float]:
        """Get wallet balances"""
        if not self.wallet:
            raise ValueError("No wallet initialized")
        return {
            "eth": float(self.wallet.default_address.balance("eth")),
            "usdc": float(self.wallet.default_address.balance("usdc"))
        }

    def request_testnet_funds(self, currency: str = "eth") -> Dict[str, Any]:
        """Request testnet funds from faucet"""
        if not self.wallet:
            raise ValueError("No wallet initialized")
        tx = self.wallet.faucet(currency)
        tx.wait()
        return {
            "transaction_id": tx.id,
            "status": tx.status
        }

    def transfer(
        self,
        amount: float,
        currency: str,
        to_address: str,
        gasless: bool = False,
        skip_batching: bool = False
    ) -> Dict[str, Any]:
        """
        Transfer funds to another address
        """
        if not self.wallet:
            raise ValueError("No wallet initialized")
        
        tx = self.wallet.transfer(
            amount,
            currency.lower(),
            to_address,
            gasless=gasless,
            skip_batching=skip_batching
        ).wait()
        
        return {
            "transaction_id": tx.id,
            "status": tx.status
        }

    def trade(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> Dict[str, Any]:
        """
        Trade between currencies
        """
        if not self.wallet:
            raise ValueError("No wallet initialized")
        
        trade = self.wallet.trade(
            amount,
            from_currency.lower(),
            to_currency.lower()
        ).wait()
        
        return {
            "trade_id": trade.id,
            "status": trade.status
        }

    def get_transfer_history(self) -> List[Dict[str, Any]]:
        """Get transfer history"""
        if not self.wallet:
            raise ValueError("No wallet initialized")
        return list(self.wallet.default_address.transfers())

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get trade history"""
        if not self.wallet:
            raise ValueError("No wallet initialized")
        return list(self.wallet.default_address.trades())

    def create_webhook(
        self,
        notification_url: str,
        event_type: str = WebhookEventType.ERC20_TRANSFER,
        network: str = None
    ) -> Dict[str, Any]:
        """Create a webhook for notifications"""
        if not self.wallet:
            raise ValueError("No wallet initialized")
        
        webhook = self.wallet.create_webhook(
            notification_url,
            event_type=event_type,
            network_id=network or self.network
        )
        
        return {
            "webhook_id": webhook.id,
            "status": webhook.status
        }

    def export_wallet(self, file_path: str, encrypt: bool = True) -> None:
        """Export wallet data to file"""
        if not self.wallet:
            raise ValueError("No wallet initialized")
        self.wallet.save_seed(file_path, encrypt=encrypt)
