"""
Junct GAME SDK Plugin — Access 20+ crypto MCP servers from any Virtuals agent.

Junct (junct.dev) hosts production MCP servers for exchanges, DeFi protocols,
oracles, and data providers. This plugin makes them available as GAME tools.
"""

from typing import Dict, List, Optional, Tuple
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
import requests

JUNCT_SERVERS = [
    {"id": "binance", "name": "Binance", "desc": "Spot exchange — trading, market data, klines, order book (340 tools)"},
    {"id": "gmx", "name": "GMX", "desc": "Perpetuals DEX on Arbitrum — positions, swaps, vaults (139 tools)"},
    {"id": "blockscout", "name": "Blockscout", "desc": "Block explorer — transactions, addresses, tokens, contracts (56 tools)"},
    {"id": "curve", "name": "Curve", "desc": "Stableswap DEX — pools, TVL, volume, gauges (43 tools)"},
    {"id": "stargate", "name": "Stargate", "desc": "Cross-chain bridge — liquidity, swaps, chain paths (42 tools)"},
    {"id": "coingecko", "name": "CoinGecko", "desc": "Market data — prices, market caps, volumes, trending (36 tools)"},
    {"id": "chainlink", "name": "Chainlink", "desc": "Oracle — price feeds, round data, aggregator (27 tools)"},
    {"id": "ens", "name": "ENS", "desc": "Name service — domain resolution, lookups (23 tools)"},
    {"id": "synthetix", "name": "Synthetix", "desc": "Synthetic assets — SNX token, staking, transfers (22 tools)"},
    {"id": "defillama", "name": "DefiLlama", "desc": "DeFi analytics — TVL, protocol data, token prices, yields (59 tools)"},
    {"id": "beefy", "name": "Beefy", "desc": "Yield optimizer — multi-chain vaults, APY data (10 tools)"},
    {"id": "maker", "name": "Maker", "desc": "Lending — DAI savings rate, DSR manager (10 tools)"},
    {"id": "compound", "name": "Compound", "desc": "Lending — supply, borrow, markets (8 tools)"},
    {"id": "eigenlayer", "name": "EigenLayer", "desc": "Restaking — delegation, operators (8 tools)"},
    {"id": "aave", "name": "Aave", "desc": "Lending — V3 pool, supply, borrow, reserves (6 tools)"},
    {"id": "lido", "name": "Lido", "desc": "Liquid staking — stETH, rates, allowances (6 tools)"},
    {"id": "jupiter", "name": "Jupiter", "desc": "Solana DEX aggregator — quotes, swaps (4 tools)"},
]


class JunctPlugin:
    """
    Junct plugin for GAME SDK.

    Provides three core tools: list available servers, discover tools on a server,
    and call any tool on any Junct-hosted MCP server.
    """

    def __init__(self, api_base: str = "https://api.junct.dev"):
        self.api_base = api_base

        self._functions: Dict[str, Function] = {
            "list_junct_servers": Function(
                fn_name="list_junct_servers",
                fn_description="List all available Junct-hosted crypto MCP servers. Returns server names, IDs, and descriptions covering exchanges, DeFi, oracles, and data providers.",
                args=[],
                hint="Use this first to see which crypto servers are available. Then use list_junct_tools to see what tools a specific server has.",
                executable=self.list_servers,
            ),
            "list_junct_tools": Function(
                fn_name="list_junct_tools",
                fn_description="List all tools available on a specific Junct MCP server. Returns tool names and descriptions.",
                args=[
                    Argument(
                        name="server_id",
                        description="The Junct server ID (e.g. 'binance', 'aave', 'chainlink'). Get IDs from list_junct_servers.",
                        type="string",
                    ),
                ],
                hint="Use this to discover what tools a server exposes before calling them with call_junct_tool.",
                executable=self.list_tools,
            ),
            "call_junct_tool": Function(
                fn_name="call_junct_tool",
                fn_description="Call a specific tool on a Junct MCP server. Pass the server ID, tool name, and any arguments the tool requires.",
                args=[
                    Argument(
                        name="server_id",
                        description="The Junct server ID (e.g. 'binance', 'aave', 'chainlink').",
                        type="string",
                    ),
                    Argument(
                        name="tool_name",
                        description="The name of the tool to call (get names from list_junct_tools).",
                        type="string",
                    ),
                    Argument(
                        name="tool_args",
                        description="JSON string of arguments to pass to the tool. Use '{}' if no arguments needed.",
                        type="string",
                        optional=True,
                    ),
                ],
                hint="First use list_junct_tools to see available tools and their parameters, then call the tool you need.",
                executable=self.call_tool,
            ),
        }

    @property
    def available_functions(self) -> List[str]:
        return list(self._functions.keys())

    def get_function(self, fn_name: str) -> Function:
        if fn_name not in self._functions:
            raise ValueError(
                f"Function '{fn_name}' not found. Available: {', '.join(self.available_functions)}"
            )
        return self._functions[fn_name]

    def _mcp_url(self, server_id: str) -> str:
        return f"https://{server_id}.mcp.junct.dev/mcp"

    def list_servers(self, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        lines = []
        for s in JUNCT_SERVERS:
            lines.append(f"- {s['id']}: {s['name']} — {s['desc']}")
        return (
            FunctionResultStatus.DONE,
            f"Available Junct servers ({len(JUNCT_SERVERS)}):\n" + "\n".join(lines),
            {"servers": [s["id"] for s in JUNCT_SERVERS]},
        )

    def list_tools(self, server_id: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        try:
            resp = requests.post(
                self._mcp_url(server_id),
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            tools = data.get("result", {}).get("tools", [])
            lines = [f"- {t['name']}: {t.get('description', '')[:100]}" for t in tools]
            return (
                FunctionResultStatus.DONE,
                f"Tools on {server_id} ({len(tools)}):\n" + "\n".join(lines),
                {"server_id": server_id, "tool_count": len(tools), "tools": [t["name"] for t in tools]},
            )
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Error listing tools for {server_id}: {str(e)}",
                {"server_id": server_id},
            )

    def call_tool(self, server_id: str, tool_name: str, tool_args: str = "{}", **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        import json as _json
        try:
            args = _json.loads(tool_args) if isinstance(tool_args, str) else tool_args
        except _json.JSONDecodeError:
            return (
                FunctionResultStatus.FAILED,
                f"Invalid JSON in tool_args: {tool_args}",
                {"server_id": server_id, "tool_name": tool_name},
            )

        try:
            resp = requests.post(
                self._mcp_url(server_id),
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": args},
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            if "error" in data:
                return (
                    FunctionResultStatus.FAILED,
                    f"MCP error: {data['error'].get('message', str(data['error']))}",
                    {"server_id": server_id, "tool_name": tool_name},
                )

            result = data.get("result", {})
            content = result.get("content", [])
            text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
            output = "\n".join(text_parts) if text_parts else _json.dumps(result, indent=2)

            return (
                FunctionResultStatus.DONE,
                output,
                {"server_id": server_id, "tool_name": tool_name},
            )
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Error calling {tool_name} on {server_id}: {str(e)}",
                {"server_id": server_id, "tool_name": tool_name},
            )
