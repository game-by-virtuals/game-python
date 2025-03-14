import time
import uuid
from membase_plugin_gamesdk.membase_plugin_gamesdk import MembasePlugin

# set your own account and agent name
# or set environment variables
default_account = "game_sdk_test"
default_agent_name = "game_sdk_test_agent"
membase_plugin = MembasePlugin(
  account=default_account,
  agent_name=default_agent_name,
  auto_upload_to_hub=True,
  preload_from_hub=True,
)

membase_plugin.add_memory("Hello, world!")
new_conversation_id = str(uuid.uuid4())
membase_plugin.switch_conversation_id(new_conversation_id)
membase_plugin.add_memory("Hello, world! 2")

time.sleep(3)

new_agent_name = "game_sdk_test_agent_new"
new_membase_plugin = MembasePlugin(
  account=default_account,
  agent_name=new_agent_name,
  auto_upload_to_hub=True,
  preload_from_hub=True,
)

res = new_membase_plugin.get_memory(new_conversation_id, 1)
if res is None:
    raise Exception("Failed to get memory none")
if len(res) != 1:
    raise Exception("Failed to get memory")
if res[0].content != "Hello, world! 2":
    raise Exception("Content is not correct")

new_membase_plugin.add_memory("Hello, world! 3")

print("Test passed")
