# Bittensor Plugin for GAME SDK

A plugin for interacting with Bittensor subnets through the GAME SDK. Currently supports image detection using subnet 34.

## Installation

```bash
pip install game-sdk
pip install -e plugins/bittensor
```

## Configuration

Set up your environment variables in a `.env` file:

```env
GAME_API_KEY=your_game_api_key
BITMIND_API_KEY=your_bitmind_api_key
```

## Usage

```python
from bittensor_game_sdk.bittensor_plugin import BittensorPlugin
# Initialize plugin
plugin = BittensorPlugin()
# Detect if an image is AI-generated
result = plugin.call_subnet(34, {"image": "https://example.com/image.jpg"})
print(f"Is AI: {result.get('isAI')}")
print(f"Confidence: {result.get('confidence')}%")
```

## Examples

```bash
python plugins/bittensor/examples/bittensor_agent.py
```

### Worker Example

The example worker (`bittensor_worker.py`) demonstrates:

- Image URL validation
- Error handling
- Integration with Bittensor subnet 34
- Basic worker configuration

### Agent Example

The example agent (`bittensor_agent.py`) shows:

- Integration with Twitter plugin
- Continuous monitoring of tweets
- Automated image analysis and responses

## API Reference

### BittensorPlugin

Main plugin class for interacting with Bittensor subnets.

Methods:

- `call_subnet(subnet_id: int, payload: Dict)`: Call a specific subnet
- `detect_image(img_url: str)`: Detect if an image is AI-generated
- `get_subnet_info(subnet_id: int)`: Get information about a subnet
- `list_subnets()`: List available subnets

### BittensorImageWorker

Example worker implementation for image detection.

Methods:

- `detect_image(image_url: str)`: Process an image through subnet 34
- `run(image_url: str)`: Run the worker on a single image

