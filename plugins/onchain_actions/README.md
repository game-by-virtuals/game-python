# Onchain Actions Plugin for Virtuals Game

The onchain actions plugin allows your GAME agents to execute onchain actions such as swaps, transfers, staking, etc. all by leveraging the [GOAT SDK](https://github.com/goat-sdk/goat).

Supports:
- Any chain, from EVM, to Solana, to Sui, etc.
- Any wallet type, from key pairs to smart wallets from Crossmint, etc.
- More than +200 onchain tools from the GOAT SDK, [see all available tools here](https://github.com/goat-sdk/goat/tree/main/python#plugins)


## Running examples

To run the examples showcased in the plugin's directory, follow these steps:

1. Create an venv
```
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```
pip install -e .
```

3. Set up environment variables:
```
export GAME_API_KEY="your-game-api-key"
export WALLET_PRIVATE_KEY="your-wallet-private-key"
export RPC_PROVIDER_URL="your-rpc-provider-url"
export UNISWAP_API_KEY=kHEhfIPvCE3PO5PeT0rNb1CA3JJcnQ8r7kJDXN5X # Public key to test with
```

4. Run example scripts:

Example worker:
```
python ./examples/example-worker.py  
```

Example agent:
```
python ./examples/example-agent.py
```
