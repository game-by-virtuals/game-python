# Conflux Plugin for GAME SDK

The Conflux Plugin enables interaction with the Conflux blockchain network, specifically designed for meme token creation and management operations.

## Features

- Create new meme tokens with customizable name, symbol, and metadata
  - With Automatic IPFS image upload and metadata management
- Retrieve list of created meme tokens

## Setup and Configuration

1. Set up the required credentials in your configuration:

```python
options = {
    "id": "conflux_plugin",  # Optional: Custom plugin ID
    "name": "Conflux Plugin",  # Optional: Custom plugin name
    "credentials": {
        # Conflux eSpace RPC URL
        "rpc_url": "https://evm.confluxrpc.com",
        # Your wallet private key
        "private_key": "YOUR_PRIVATE_KEY", 
        # Meme contract address,
        # mainnet 0x4b892680caf3b6d63e0281bf1858d92d0a7ba90b
        # testnet 0xA016695B5E633399027Ec36941ECa4D5601aBEac
        "contract_address": "CONTRACT_ADDRESS",
        # serverless function deployment (https://github.com/darwintree/confi-pump-helper).
        # mainnet https://eliza-helper.vercel.app
        # testnet https://eliza-helper-test.vercel.app
        "confi_pump_helper_url": "HELPER_URL",  # Confi Pump Helper service URL
    }
}
```

1. Initialize the plugin
 
```python
from conflux_plugin_gamesdk.conflux_plugin_gamesdk import ConfluxPlugin

conflux_plugin = ConfluxPlugin(options)
```

## Available Functions

1. `create_meme(name: str, symbol: str, description: str, image_url: str)`
   - Creates a new meme token with specified parameters
   - Automatically uploads image to IPFS
   - Returns the deployed token contract address
   - Each creation would cost **10 CFX**
   
2. `get_meme_list()`
   - Retrieves the list of all created meme tokens
   - Returns token information list including addresses and metadata

```python
class MemeInfo(TypedDict):
    address: str
    name: str
    symbol: str
    description: str
    progress: str  # a float in string, 0~100
```

## Example Usage

```python
# Create a new meme token
create_meme_func = conflux_plugin.get_function("create_meme")
token_address = create_meme_func(
    name="MyMeme",
    symbol="MEME",
    description="My awesome meme token",
    image_url="https://example.com/meme.jpg"
)

# Get list of meme tokens
get_meme_list_func = conflux_plugin.get_function("get_meme_list")
meme_list = get_meme_list_func()
```

## Requirements

- Requires serverless function to be deployed (https://github.com/darwintree/confi-pump-helper)
- Web3.py for blockchain interactions
- Active Conflux eSpace network connection
- Sufficient CFX balance for token creation (10 CFX required per token)

## Network Support

- Default: Conflux eSpace Mainnet/testnet, depending on configuration

## Notes

- Token creation includes automatic IPFS upload with safe block confirmation
- Image uploads are handled asynchronously after transaction confirmation
