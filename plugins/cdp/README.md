# Coinbase Developer Platform (CDP) Plugin for GAME SDK

A plugin for interacting with Coinbase's CDP through the GAME SDK. This plugin provides a simple interface for wallet management, transfers, trading, and webhooks on Base network.

## Features

- Wallet Management (create, import, export)
- Gasless USDC Transfers
- ETH/USDC Trading
- Webhook Integration
- Transfer/Trade History
- Testnet Faucet Support
- Base Network Support (Sepolia testnet & mainnet)

## Installation

```bash
# Install from local directory
pip install -e plugins/cdp

# Dependencies will be installed automatically:
# - game-sdk>=0.1.1
# - cdp-sdk>=0.16.0
# - python-dotenv>=1.0.0
```

## Configuration

Set up your environment variables in a `.env` file:

```env
# Required
GAME_API_KEY=your_game_api_key
CDP_API_KEY_NAME=your_cdp_api_key_name
CDP_API_KEY_PRIVATE_KEY=your_cdp_api_key_private_key
```

## Basic Usage

```python
from cdp_game_sdk.cdp_plugin import CDPPlugin

# Initialize plugin
plugin = CDPPlugin()
plugin.initialize()

# Create and fund a wallet
wallet = plugin.create_wallet()
print(f"New wallet created: {wallet['address']}")

# Request testnet funds
plugin.request_testnet_funds("eth")
plugin.request_testnet_funds("usdc")

# Check balances
balances = plugin.get_wallet_balance()
print(f"ETH: {balances['eth']}")
print(f"USDC: {balances['usdc']}")

# Transfer USDC (gasless)
plugin.transfer(
    amount=0.1,
    currency="usdc",
    to_address="0x123...",
    gasless=True
)

# Trade ETH for USDC
plugin.trade(
    amount=0.1,
    from_currency="eth",
    to_currency="usdc"
)
```

## Examples

The plugin comes with two example implementations:

### CDP Worker

```python
from cdp_game_sdk.cdp_plugin import CDPPlugin
from examples.cdp_worker import CDPWorker

worker = CDPWorker()

# Create and fund a wallet
worker.run("create_and_fund_wallet")

# Transfer USDC
worker.run("transfer_usdc", 
    to_address="0x123...", 
    amount=10.0
)

# Trade ETH for USDC
worker.run("trade_eth_for_usdc", 
    amount=0.1
)
```

### CDP Agent

```python
from examples.cdp_agent import main as run_agent

# Starts a monitoring agent that:
# - Maintains minimum ETH/USDC balances
# - Monitors transfers
# - Creates webhooks for notifications
run_agent()
```

## API Reference

### CDPPlugin

Main plugin class for interacting with CDP.

#### Initialization
```python
plugin = CDPPlugin()
plugin.initialize(use_server_signer=False)
```

#### Methods

**Wallet Management**
- `create_wallet()`: Create new wallet
- `import_wallet(wallet_id: str, seed_file: str)`: Import existing wallet
- `export_wallet(file_path: str, encrypt: bool)`: Export wallet data
- `get_wallet_balance()`: Get ETH and USDC balances

**Transactions**
- `transfer(amount: float, currency: str, to_address: str, gasless: bool)`: Transfer funds
- `trade(amount: float, from_currency: str, to_currency: str)`: Trade between currencies
- `request_testnet_funds(currency: str)`: Request testnet funds from faucet

**Monitoring**
- `get_transfer_history()`: Get list of transfers
- `get_trade_history()`: Get list of trades
- `create_webhook(notification_url: str)`: Create notification webhook

## Development

Run tests:
```bash
pytest plugins/coinbase/test_cdp.py -v
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Run tests and add new ones
4. Submit a pull request

## Support

- Documentation: [CDP Documentation](https://docs.cloud.coinbase.com/cdp/docs)
- Issues: [GitHub Issues](https://github.com/game-by-virtuals/game-python/issues)
