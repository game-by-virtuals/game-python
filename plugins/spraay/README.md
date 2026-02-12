# Spraay Plugin for GAME SDK

**Batch crypto payments for AI agents on Base.**

Give your [GAME](https://docs.game.virtuals.io/)-powered AI agents the ability to send ETH and ERC-20 tokens to up to 200 recipients in a single transaction using the [Spraay](https://spraay.app) smart contract on Base.

## Why Spraay?

- **~80% gas savings** vs individual transfers
- **200 recipients** per transaction
- **ETH + any ERC-20** (USDC, DAI, WETH, etc.)
- **0.3% protocol fee** — no subscriptions, no minimums
- **Verified on BaseScan** — OpenZeppelin security (ReentrancyGuard + Pausable)

## Installation

```bash
pip install spraay-plugin-gamesdk
```

Or install from source:

```bash
git clone https://github.com/plagtech/spraay-game-plugin.git
cd spraay-game-plugin
pip install -e .
```

## Quick Start

### As a Worker (add to existing agent)

```python
from spraay_plugin_gamesdk import SpraayPlugin
from game_sdk.game.agent import WorkerConfig

spraay = SpraayPlugin(private_key="0x...")

spraay_worker = WorkerConfig(
    id="batch_payments",
    worker_description="Batch payment worker powered by Spraay on Base.",
    action_space=spraay.get_tools(),
    get_state_fn=lambda: {"wallet": spraay.wallet_address},
)

# Add spraay_worker to your agent's workers list
```

### Standalone Agent

```python
from spraay_plugin_gamesdk import SpraayPlugin
from game_sdk.game.agent import Agent, WorkerConfig

spraay = SpraayPlugin(private_key="0x...")

agent = Agent(
    api_key="your_game_api_key",
    name="Payment Agent",
    agent_goal="Batch-send crypto payments efficiently on Base.",
    agent_description="AI agent with Spraay batch payment capabilities.",
    workers=[
        WorkerConfig(
            id="spraay_worker",
            worker_description="Handles batch ETH and token payments.",
            action_space=spraay.get_tools(),
        ),
    ],
)

agent.compile()
agent.run(60, {"verbose": True})
```

## Available Functions

| Function | Description |
|---|---|
| `spraay_batch_eth` | Send variable ETH amounts to multiple recipients |
| `spraay_batch_eth_equal` | Send equal ETH to multiple recipients |
| `spraay_batch_erc20` | Send variable ERC-20 amounts to multiple recipients |
| `spraay_batch_erc20_equal` | Send equal ERC-20 to multiple recipients |
| `spraay_check_balance` | Check ETH and token balances |
| `spraay_estimate_cost` | Estimate total cost before sending |

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SPRAAY_PRIVATE_KEY` | Yes | Wallet private key for signing transactions |
| `BASE_RPC_URL` | No | Base RPC endpoint (default: `https://mainnet.base.org`) |
| `GAME_API_KEY` | Yes* | GAME API key (*only if running a GAME agent) |

## Supported Tokens

Built-in shortcuts for common Base tokens:

| Symbol | Address |
|---|---|
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| DAI | `0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb` |
| WETH | `0x4200000000000000000000000000000000000006` |
| cbETH | `0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22` |
| USDbC | `0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA` |

You can also use any ERC-20 token by passing its contract address directly.

## Contract

- **Address:** `0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC`
- **Network:** Base Mainnet (Chain ID: 8453)
- **BaseScan:** [View Contract](https://basescan.org/address/0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC)

## Use Cases

- **DAO Payroll** — Agent pays team members monthly
- **Airdrop Distribution** — Agent sprays tokens to community wallets
- **Bounty Payments** — Agent rewards contributors with variable amounts
- **Revenue Sharing** — Agent distributes earnings to stakeholders
- **Agent-to-Agent Commerce** — Spraay as settlement layer in ACP workflows

## Links

- **Website:** [spraay.app](https://spraay.app)
- **GitHub:** [github.com/plagtech](https://github.com/plagtech)
- **Twitter:** [@lostpoet](https://twitter.com/lostpoet)
- **Farcaster:** [@plag](https://warpcast.com/plag)

## License

MIT
