from typing import Tuple
from game_sdk.game.custom_types import FunctionResultStatus
from allora_game_sdk.allora_plugin import AlloraPlugin
from allora_sdk.v2.api_client import ChainSlug

def print_function_result(function_result: Tuple[FunctionResultStatus, str, dict]):
    status, message, data = function_result
    print(f"Status: {status}")
    print(f"Message: {message}")
    print(f"Data: {data}")

allora_network_plugin = AlloraPlugin(
  chain_slug=ChainSlug.TESTNET
)

# Get all topics
print("1. Fetching all topics...")
all_topics_result = allora_network_plugin.get_all_topics()
print_function_result(all_topics_result)
print("-" * 100)

# Get inference by topic id
print("2. Fetching inference by topic id...")
inference_result = allora_network_plugin.get_inference_by_topic_id(topic_id=1)
print_function_result(inference_result)
print("-" * 100)

# Get price inference
print("3. Fetching price inference...")
price_inference = allora_network_plugin.get_price_inference(asset="BTC", timeframe="5m")
print_function_result(price_inference)
print("-" * 100)
