"""SCDO x402 wallet for Virtuals GAME SDK (game_sdk) agents.

    pip install -e plugins/scdo   # from the game-python repo root

    from scdo_plugin_gamesdk import ScdoWalletPlugin
    scdo = ScdoWalletPlugin(bot="my-game-agent")          # local key, own USDC wallet on Base
    worker = scdo.get_worker()                            # WorkerConfig for Agent(workers=[...])
    # or add scdo.get_functions() to your own worker's action_space

Keys are generated locally by the scdo-agent CLI (auto-downloaded on Linux into ~/.scdo-agent) and never leave the data dir.
Payments: x402 EIP-3009 USDC on Base, caps 0.001 to 1 USDC per payment, 100 payments and 20 USDC per day.
Every register, wallet, payment and income is a signed row on the SCDO x402 Agent Ledger: https://scdo.com.au/agent-ledger/
"""
from __future__ import annotations

import os
import re
from typing import Any, Callable, Optional

from .core import CAPS_TEXT, ScdoAgent, ScdoError

try:
    from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
except ImportError as e:  # pragma: no cover
    raise ImportError('game_sdk is required: pip install game_sdk') from e


def _slug(s: str) -> str:
    n = re.sub(r"[^a-z0-9_.-]+", "-", (s or "").lower()).lstrip("-._")[:64]
    return n or "game-agent"


class ScdoWalletPlugin:
    """GAME functions: scdo_register_agent, scdo_create_wallet, scdo_get_balance, scdo_pay_x402, scdo_book_income."""

    def __init__(self, bot: Optional[str] = None, agent: Optional[ScdoAgent] = None, network: Optional[str] = None,
                 max_usdc: str = "0.10", daily_usdc: str = "1.00", autostart: bool = False):
        self.bot = _slug(bot or os.environ.get("SCDO_AGENT_BOT") or "game-agent")
        self.agent = agent or ScdoAgent(network=network)
        self.max_usdc, self.daily_usdc = max_usdc, daily_usdc
        if autostart:
            self.ensure()

    def ensure(self) -> dict:
        """Register (signed heartbeats) and create the Base USDC wallet if missing. Idempotent."""
        r = self.agent.register_agent(self.bot)
        if not self.agent.wallet_doc(self.bot):
            r["wallet"] = self.agent.create_wallet(self.bot, max_usdc=self.max_usdc, daily_usdc=self.daily_usdc)["wallet"]
        else:
            r["wallet"] = self.agent.wallet_doc(self.bot).get("address")
        return r

    def _wrap(self, fn: Callable[..., dict], ok: Callable[[dict], str]) -> Callable[..., tuple]:
        def run(**kw: Any):
            try:
                d = fn(**{k: v for k, v in kw.items() if v not in (None, "")})
                return FunctionResultStatus.DONE, ok(d), d
            except ScdoError as e:
                return FunctionResultStatus.FAILED, f"SCDO wallet: {e.code}: {e}", {"error": e.code}
            except Exception as e:  # noqa: BLE001
                return FunctionResultStatus.FAILED, f"SCDO wallet: {e}", {"error": "exception"}
        return run

    def get_functions(self) -> list:
        a, b = self.agent, self.bot
        return [
            Function(fn_name="scdo_register_agent", fn_description="Create or reuse this agent's SCDO identity and its x402 USDC wallet on Base, and start signed heartbeats to the SCDO x402 Agent Ledger.",
                     args=[], executable=self._wrap(lambda: self.ensure(), lambda d: f"SCDO agent {d['name']} ({d['agent']}), wallet {d.get('wallet')}.")),
            Function(fn_name="scdo_create_wallet", fn_description="Create or reuse this agent's x402 wallet (USDC on Base mainnet) and bind it on the Agent Ledger.",
                     args=[Argument(name="network", description="base (default) or base-sepolia", type="string", optional=True)],
                     executable=self._wrap(lambda network=None: a.create_wallet(b, network=network, max_usdc=self.max_usdc, daily_usdc=self.daily_usdc), lambda d: f"x402 wallet {d['wallet']} on {d['networkLabel']}. {d['fundWith']}")),
            Function(fn_name="scdo_get_balance", fn_description="Show the agent wallet's on-chain USDC and its Agent Ledger balances.",
                     args=[], executable=self._wrap(lambda: a.get_balance(b), lambda d: f"Wallet {d.get('wallet')}: {(d.get('onchainUsdc') or {}).get('usdc', '?')} USDC on chain.")),
            Function(fn_name="scdo_pay_x402", fn_description=f"Pay an x402 (HTTP 402) URL from the agent's USDC wallet and get the resource. Caps: {CAPS_TEXT}.",
                     args=[Argument(name="url", description="https URL that answers HTTP 402 with x402 requirements", type="string"),
                           Argument(name="max_usdc", description="most USDC to pay, e.g. 0.05 (default 0.10)", type="string", optional=True)],
                     executable=self._wrap(lambda url, max_usdc=None: a.pay_x402(b, url, max_usdc=max_usdc or self.max_usdc), lambda d: f"Paid {d.get('amountUsdc')} USDC to {d.get('payTo')}. Transaction {d.get('tx')}.")),
            Function(fn_name="scdo_book_income", fn_description="Book a settled x402 payment this agent received as income on the Agent Ledger.",
                     args=[Argument(name="payment_payload", description="X-PAYMENT payload (base64 or JSON)", type="string"),
                           Argument(name="settlement", description="settlement response (base64 or JSON)", type="string")],
                     executable=self._wrap(lambda payment_payload, settlement: a.book_income(payment_payload, settlement, bot=b), lambda d: f"Income booked (entry {d['entry']['id']}).")),
        ]

    def get_state(self, function_result: Any = None, current_state: Any = None) -> dict:
        doc = None
        try:
            doc = self.agent.wallet_doc(self.bot)
        except Exception:  # noqa: BLE001
            doc = None
        return {"scdo_bot": self.bot, "scdo_wallet": (doc or {}).get("address"), "scdo_network": (doc or {}).get("network"), "caps": CAPS_TEXT}

    def get_worker(self, worker_id: str = "scdo_wallet_worker"):
        from game_sdk.game.agent import WorkerConfig
        return WorkerConfig(id=worker_id, worker_description="Holds this agent's own SCDO x402 USDC wallet on Base: registers on the SCDO x402 Agent Ledger, pays x402 URLs and books income.",
                            get_state_fn=self.get_state, action_space=self.get_functions())


def get_functions(bot: Optional[str] = None, **kw: Any) -> list:
    return ScdoWalletPlugin(bot=bot, **kw).get_functions()
