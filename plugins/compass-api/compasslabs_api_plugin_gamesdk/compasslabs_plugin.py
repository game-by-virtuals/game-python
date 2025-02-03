from compass.virtuals_sdk import *

# example usuage:
# 1. 
# simple_agent.compass_agent.compile()
# simple_agent.compass_agent.run()
# 2. 
# simple_workers.others_compass_api_worker.run("get the details of the ENS name vitalik.eth")
# 3.
# (Directly call an executable from api_wrapper.UniswapV3, api_wrapper.Others, api_wrapper.AaveV3, api_wrapper.Aerodrome, wallet.Wallet)

# Each of the classes mentioned under (3) have suggestions for inputs to a Worker or WorkerConfig, e.g. actions_space, id, worker_description.
# e.g.. [api_wrapper.Others.action_space] is a list of [Function]s that you would pass when constructing a WorkerConfig.
