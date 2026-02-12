"""
Spraay Plugin for GAME SDK by Virtuals Protocol

Enables AI agents to batch-send ETH and ERC-20 tokens to multiple recipients
in a single transaction on Base, using the Spraay smart contract.

Contract: 0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC (Base Mainnet)
Docs: https://spraay.app
GitHub: https://github.com/plagtech
"""

import json
import os
from typing import Any, Dict, List, Tuple

from web3 import Web3
from game_sdk.game.custom_types import Function, Argument, FunctionResultStatus


# Spraay contract addresses
SPRAAY_CONTRACT_BASE = "0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC"

# Default RPC
BASE_MAINNET_RPC = "https://mainnet.base.org"

# Spraay contract ABI (minimal - only the functions we need)
SPRAAY_ABI = json.loads("""[
    {
        "inputs": [
            {"internalType": "address payable[]", "name": "recipients", "type": "address[]"},
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "name": "batchSendETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "address[]", "name": "recipients", "type": "address[]"},
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "name": "batchSendERC20",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "serviceFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "paused",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]""")

# ERC-20 ABI (minimal - approve + balanceOf + decimals + symbol)
ERC20_ABI = json.loads("""[
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]""")

# Common Base tokens
KNOWN_TOKENS = {
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
    "WETH": "0x4200000000000000000000000000000000000006",
    "cbETH": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
    "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
}


class SpraayPlugin:
    """
    Spraay Plugin for GAME SDK.

    Gives AI agents the ability to batch-send ETH and ERC-20 tokens
    to multiple recipients in a single transaction on Base.

    Usage:
        plugin = SpraayPlugin(private_key="0x...")
        tools = plugin.get_tools()
        # Pass tools to a GAME Worker's action space
    """

    def __init__(
        self,
        private_key: str = None,
        rpc_url: str = None,
        contract_address: str = None,
    ):
        """
        Initialize the Spraay plugin.

        Args:
            private_key: Private key for signing transactions.
                         Falls back to SPRAAY_PRIVATE_KEY env var.
            rpc_url: Base RPC URL. Falls back to BASE_RPC_URL env var
                     or default public RPC.
            contract_address: Spraay contract address. Defaults to
                              Base mainnet deployment.
        """
        self.private_key = private_key or os.environ.get("SPRAAY_PRIVATE_KEY", "")
        self.rpc_url = rpc_url or os.environ.get("BASE_RPC_URL", BASE_MAINNET_RPC)
        self.contract_address = Web3.to_checksum_address(
            contract_address or SPRAAY_CONTRACT_BASE
        )

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.contract = self.w3.eth.contract(
            address=self.contract_address, abi=SPRAAY_ABI
        )

        # Derive wallet address from private key
        if self.private_key:
            self.wallet_address = self.w3.eth.account.from_key(
                self.private_key
            ).address
        else:
            self.wallet_address = None

        # Build function registry
        self.functions: Dict[str, Function] = {
            "spraay_batch_eth": Function(
                fn_name="spraay_batch_eth",
                fn_description=(
                    "Batch-send ETH to multiple recipients in a single transaction "
                    "on Base using the Spraay smart contract. Saves ~80% on gas vs "
                    "individual transfers. Supports up to 200 recipients per tx."
                ),
                hint=(
                    "Use this when you need to pay multiple wallets at once. "
                    "Provide recipients as comma-separated addresses and amounts "
                    "in ETH (not wei). Example: recipients='0xABC...,0xDEF...' "
                    "amounts='0.01,0.02'"
                ),
                executable=self.batch_send_eth,
                args=[
                    Argument(
                        name="recipients",
                        description=(
                            "Comma-separated list of recipient wallet addresses. "
                            "Example: '0xABC...,0xDEF...,0x123...'"
                        ),
                        type="string",
                    ),
                    Argument(
                        name="amounts",
                        description=(
                            "Comma-separated list of ETH amounts to send to each "
                            "recipient. Must match the number of recipients. "
                            "Example: '0.01,0.02,0.015'"
                        ),
                        type="string",
                    ),
                ],
            ),
            "spraay_batch_eth_equal": Function(
                fn_name="spraay_batch_eth_equal",
                fn_description=(
                    "Batch-send an equal amount of ETH to multiple recipients in a "
                    "single transaction on Base. Useful for airdrops, equal-split "
                    "payouts, and bounty distributions."
                ),
                hint=(
                    "Use this when every recipient gets the same amount. "
                    "Example: recipients='0xABC...,0xDEF...' amount='0.01'"
                ),
                executable=self.batch_send_eth_equal,
                args=[
                    Argument(
                        name="recipients",
                        description=(
                            "Comma-separated list of recipient wallet addresses."
                        ),
                        type="string",
                    ),
                    Argument(
                        name="amount",
                        description=(
                            "Amount of ETH each recipient will receive. "
                            "Example: '0.01'"
                        ),
                        type="string",
                    ),
                ],
            ),
            "spraay_batch_erc20": Function(
                fn_name="spraay_batch_erc20",
                fn_description=(
                    "Batch-send ERC-20 tokens (USDC, DAI, WETH, or any token) "
                    "to multiple recipients in a single transaction on Base. "
                    "Automatically handles token approval if needed."
                ),
                hint=(
                    "Use this for batch token distributions. You can use token "
                    "symbols (USDC, DAI, WETH) or contract addresses. "
                    "Amounts should be in human-readable units (e.g., '10' for "
                    "10 USDC, not in wei)."
                ),
                executable=self.batch_send_erc20,
                args=[
                    Argument(
                        name="token",
                        description=(
                            "Token symbol (USDC, DAI, WETH, cbETH, USDbC) or "
                            "token contract address."
                        ),
                        type="string",
                    ),
                    Argument(
                        name="recipients",
                        description=(
                            "Comma-separated list of recipient wallet addresses."
                        ),
                        type="string",
                    ),
                    Argument(
                        name="amounts",
                        description=(
                            "Comma-separated list of token amounts for each "
                            "recipient in human-readable units. "
                            "Example: '10,20,15' for USDC"
                        ),
                        type="string",
                    ),
                ],
            ),
            "spraay_batch_erc20_equal": Function(
                fn_name="spraay_batch_erc20_equal",
                fn_description=(
                    "Batch-send an equal amount of ERC-20 tokens to multiple "
                    "recipients in a single transaction on Base."
                ),
                hint=(
                    "Use this for equal-split token distributions like airdrops. "
                    "Example: token='USDC' recipients='0xABC...,0xDEF...' amount='10'"
                ),
                executable=self.batch_send_erc20_equal,
                args=[
                    Argument(
                        name="token",
                        description="Token symbol or contract address.",
                        type="string",
                    ),
                    Argument(
                        name="recipients",
                        description="Comma-separated list of recipient addresses.",
                        type="string",
                    ),
                    Argument(
                        name="amount",
                        description=(
                            "Amount each recipient receives in human-readable units."
                        ),
                        type="string",
                    ),
                ],
            ),
            "spraay_check_balance": Function(
                fn_name="spraay_check_balance",
                fn_description=(
                    "Check the agent's ETH balance and optionally an ERC-20 token "
                    "balance on Base. Use this before sending to ensure sufficient funds."
                ),
                hint="Call this before batch sending to verify you have enough funds.",
                executable=self.check_balance,
                args=[
                    Argument(
                        name="token",
                        description=(
                            "Optional: Token symbol or address to check balance of. "
                            "Leave empty to check only ETH balance."
                        ),
                        type="string",
                        optional=True,
                    ),
                ],
            ),
            "spraay_estimate_cost": Function(
                fn_name="spraay_estimate_cost",
                fn_description=(
                    "Estimate the total cost of a batch ETH send including the "
                    "0.3% Spraay protocol fee and gas. Use before executing to "
                    "preview costs."
                ),
                hint="Always estimate before sending to avoid insufficient funds errors.",
                executable=self.estimate_cost,
                args=[
                    Argument(
                        name="recipients_count",
                        description="Number of recipients in the batch.",
                        type="string",
                    ),
                    Argument(
                        name="total_amount",
                        description="Total ETH amount to distribute.",
                        type="string",
                    ),
                ],
            ),
        }

    def get_tools(self) -> List[Function]:
        """Returns all available Spraay functions for GAME Worker integration."""
        return list(self.functions.values())

    # ── Helpers ──────────────────────────────────────────────────────

    def _parse_addresses(self, recipients: str) -> List[str]:
        """Parse comma-separated addresses into checksummed list."""
        addrs = [a.strip() for a in recipients.split(",") if a.strip()]
        return [Web3.to_checksum_address(a) for a in addrs]

    def _parse_amounts_eth(self, amounts: str) -> List[int]:
        """Parse comma-separated ETH amounts into wei."""
        return [Web3.to_wei(float(a.strip()), "ether") for a in amounts.split(",") if a.strip()]

    def _resolve_token(self, token: str) -> str:
        """Resolve token symbol to address, or validate address."""
        upper = token.upper().strip()
        if upper in KNOWN_TOKENS:
            return KNOWN_TOKENS[upper]
        # Assume it's an address
        return Web3.to_checksum_address(token.strip())

    def _get_token_decimals(self, token_address: str) -> int:
        """Get token decimals."""
        token_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
        )
        return token_contract.functions.decimals().call()

    def _get_token_symbol(self, token_address: str) -> str:
        """Get token symbol."""
        token_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
        )
        try:
            return token_contract.functions.symbol().call()
        except Exception:
            return "UNKNOWN"

    def _ensure_wallet(self) -> bool:
        """Check that wallet is configured."""
        return bool(self.private_key and self.wallet_address)

    def _send_tx(self, tx: dict) -> str:
        """Sign and send a transaction, return tx hash."""
        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt["status"] != 1:
            raise Exception(f"Transaction reverted: {tx_hash.hex()}")
        return tx_hash.hex()

    # ── Core Functions ───────────────────────────────────────────────

    def batch_send_eth(
        self, recipients: str, amounts: str, **kwargs
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Batch send variable amounts of ETH to multiple recipients."""
        if not self._ensure_wallet():
            return (
                FunctionResultStatus.FAILED,
                "No wallet configured. Set SPRAAY_PRIVATE_KEY environment variable.",
                {},
            )

        try:
            addr_list = self._parse_addresses(recipients)
            amount_list = self._parse_amounts_eth(amounts)

            if len(addr_list) != len(amount_list):
                return (
                    FunctionResultStatus.FAILED,
                    f"Mismatch: {len(addr_list)} recipients but {len(amount_list)} amounts.",
                    {},
                )

            if len(addr_list) > 200:
                return (
                    FunctionResultStatus.FAILED,
                    f"Too many recipients ({len(addr_list)}). Maximum is 200 per transaction.",
                    {},
                )

            total_amount = sum(amount_list)
            # 0.3% service fee
            service_fee = total_amount * 30 // 10000
            total_value = total_amount + service_fee

            # Build transaction
            tx = self.contract.functions.batchSendETH(
                addr_list, amount_list
            ).build_transaction({
                "from": self.wallet_address,
                "value": total_value,
                "nonce": self.w3.eth.get_transaction_count(self.wallet_address),
                "gas": 21000 + (28000 * len(addr_list)),  # estimate
                "maxFeePerGas": self.w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": self.w3.to_wei(0.001, "gwei"),
                "chainId": 8453,  # Base
            })

            tx_hash = self._send_tx(tx)

            total_eth = Web3.from_wei(total_amount, "ether")
            fee_eth = Web3.from_wei(service_fee, "ether")

            return (
                FunctionResultStatus.DONE,
                (
                    f"Successfully sprayed {total_eth} ETH to {len(addr_list)} "
                    f"recipients. Service fee: {fee_eth} ETH. "
                    f"Tx: https://basescan.org/tx/0x{tx_hash}"
                ),
                {
                    "tx_hash": f"0x{tx_hash}",
                    "recipients_count": len(addr_list),
                    "total_eth": str(total_eth),
                    "service_fee_eth": str(fee_eth),
                    "basescan_url": f"https://basescan.org/tx/0x{tx_hash}",
                },
            )
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Batch ETH send failed: {str(e)}",
                {},
            )

    def batch_send_eth_equal(
        self, recipients: str, amount: str, **kwargs
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Batch send equal ETH amounts to multiple recipients."""
        try:
            addr_list = self._parse_addresses(recipients)
            per_amount = Web3.to_wei(float(amount.strip()), "ether")
            amounts_str = ",".join([amount.strip()] * len(addr_list))
            return self.batch_send_eth(recipients, amounts_str, **kwargs)
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Equal ETH send failed: {str(e)}",
                {},
            )

    def batch_send_erc20(
        self, token: str, recipients: str, amounts: str, **kwargs
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Batch send variable amounts of ERC-20 tokens to multiple recipients."""
        if not self._ensure_wallet():
            return (
                FunctionResultStatus.FAILED,
                "No wallet configured. Set SPRAAY_PRIVATE_KEY environment variable.",
                {},
            )

        try:
            token_address = self._resolve_token(token)
            addr_list = self._parse_addresses(recipients)
            decimals = self._get_token_decimals(token_address)
            symbol = self._get_token_symbol(token_address)

            # Parse amounts with correct decimals
            raw_amounts = [a.strip() for a in amounts.split(",") if a.strip()]
            amount_list = [int(float(a) * (10 ** decimals)) for a in raw_amounts]

            if len(addr_list) != len(amount_list):
                return (
                    FunctionResultStatus.FAILED,
                    f"Mismatch: {len(addr_list)} recipients but {len(amount_list)} amounts.",
                    {},
                )

            if len(addr_list) > 200:
                return (
                    FunctionResultStatus.FAILED,
                    f"Too many recipients ({len(addr_list)}). Maximum is 200 per transaction.",
                    {},
                )

            total_amount = sum(amount_list)

            # Check and set approval
            token_contract = self.w3.eth.contract(
                address=token_address, abi=ERC20_ABI
            )
            current_allowance = token_contract.functions.allowance(
                self.wallet_address, self.contract_address
            ).call()

            if current_allowance < total_amount:
                approve_tx = token_contract.functions.approve(
                    self.contract_address, total_amount
                ).build_transaction({
                    "from": self.wallet_address,
                    "nonce": self.w3.eth.get_transaction_count(self.wallet_address),
                    "gas": 60000,
                    "maxFeePerGas": self.w3.eth.gas_price * 2,
                    "maxPriorityFeePerGas": self.w3.to_wei(0.001, "gwei"),
                    "chainId": 8453,
                })
                self._send_tx(approve_tx)

            # Build batch send transaction
            tx = self.contract.functions.batchSendERC20(
                token_address, addr_list, amount_list
            ).build_transaction({
                "from": self.wallet_address,
                "nonce": self.w3.eth.get_transaction_count(self.wallet_address),
                "gas": 50000 + (35000 * len(addr_list)),
                "maxFeePerGas": self.w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": self.w3.to_wei(0.001, "gwei"),
                "chainId": 8453,
            })

            tx_hash = self._send_tx(tx)

            total_human = sum(float(a) for a in raw_amounts)

            return (
                FunctionResultStatus.DONE,
                (
                    f"Successfully sprayed {total_human} {symbol} to "
                    f"{len(addr_list)} recipients. "
                    f"Tx: https://basescan.org/tx/0x{tx_hash}"
                ),
                {
                    "tx_hash": f"0x{tx_hash}",
                    "token": symbol,
                    "token_address": token_address,
                    "recipients_count": len(addr_list),
                    "total_amount": str(total_human),
                    "basescan_url": f"https://basescan.org/tx/0x{tx_hash}",
                },
            )
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Batch ERC-20 send failed: {str(e)}",
                {},
            )

    def batch_send_erc20_equal(
        self, token: str, recipients: str, amount: str, **kwargs
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Batch send equal ERC-20 amounts to multiple recipients."""
        try:
            addr_list = self._parse_addresses(recipients)
            amounts_str = ",".join([amount.strip()] * len(addr_list))
            return self.batch_send_erc20(token, recipients, amounts_str, **kwargs)
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Equal ERC-20 send failed: {str(e)}",
                {},
            )

    def check_balance(
        self, token: str = "", **kwargs
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Check ETH and optionally token balance."""
        if not self._ensure_wallet():
            return (
                FunctionResultStatus.FAILED,
                "No wallet configured. Set SPRAAY_PRIVATE_KEY environment variable.",
                {},
            )

        try:
            eth_balance = self.w3.eth.get_balance(self.wallet_address)
            eth_human = float(Web3.from_wei(eth_balance, "ether"))

            result = {
                "wallet": self.wallet_address,
                "eth_balance": str(eth_human),
            }
            msg = f"Wallet {self.wallet_address}: {eth_human:.6f} ETH"

            if token and token.strip():
                token_address = self._resolve_token(token)
                token_contract = self.w3.eth.contract(
                    address=token_address, abi=ERC20_ABI
                )
                decimals = token_contract.functions.decimals().call()
                symbol = self._get_token_symbol(token_address)
                raw_balance = token_contract.functions.balanceOf(
                    self.wallet_address
                ).call()
                token_balance = raw_balance / (10 ** decimals)
                result["token_symbol"] = symbol
                result["token_balance"] = str(token_balance)
                msg += f", {token_balance:.6f} {symbol}"

            return (FunctionResultStatus.DONE, msg, result)
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Balance check failed: {str(e)}",
                {},
            )

    def estimate_cost(
        self, recipients_count: str, total_amount: str, **kwargs
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """Estimate total cost of a batch ETH send."""
        try:
            count = int(recipients_count)
            amount = float(total_amount)

            if count > 200:
                return (
                    FunctionResultStatus.FAILED,
                    f"Maximum 200 recipients per transaction. Got {count}.",
                    {},
                )

            service_fee = amount * 0.003  # 0.3%
            # Rough gas estimate
            estimated_gas = 21000 + (28000 * count)
            gas_price_gwei = 0.01  # Base is very cheap
            gas_cost_eth = (estimated_gas * gas_price_gwei) / 1e9

            total_cost = amount + service_fee + gas_cost_eth

            return (
                FunctionResultStatus.DONE,
                (
                    f"Estimated cost for spraying {amount} ETH to {count} recipients: "
                    f"Amount: {amount} ETH, "
                    f"Service fee (0.3%): {service_fee:.6f} ETH, "
                    f"Est. gas: ~{gas_cost_eth:.6f} ETH, "
                    f"Total: ~{total_cost:.6f} ETH"
                ),
                {
                    "recipients_count": count,
                    "send_amount": str(amount),
                    "service_fee": f"{service_fee:.6f}",
                    "estimated_gas_eth": f"{gas_cost_eth:.6f}",
                    "estimated_total": f"{total_cost:.6f}",
                },
            )
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Cost estimation failed: {str(e)}",
                {},
            )
