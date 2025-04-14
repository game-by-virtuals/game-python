from typing import Any,Tuple
import os
from twitter_plugin_gamesdk.game_twitter_plugin import GameTwitterPlugin
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AcpPluginOptions
from acp_plugin_gamesdk.acp_token import AcpToken
from acp_plugin_gamesdk.interface import AcpClusters
from game_sdk.game.custom_types import Argument, Function, FunctionResult, FunctionResultStatus
from game_sdk.game.agent import Agent, WorkerConfig

def ask_question(query: str) -> str:
    return input(query)

# GAME Twitter Plugin options
options = {
    "id": "test_game_twitter_plugin",
    "name": "Test GAME Twitter Plugin",
    "description": "An example GAME Twitter Plugin for testing.",
    "credentials": {
        "gameTwitterAccessToken": os.environ.get("GAME_TWITTER_ACCESS_TOKEN_SELLER")
    },
}

# NativeTwitter Plugin options
# options = {
#     "id": "test_twitter_plugin",
#     "name": "Test Twitter Plugin",
#     "description": "An example Twitter Plugin for testing.",
#     "credentials": {
#         "bearerToken": os.environ.get("TWITTER_BEARER_TOKEN"),
#         "apiKey": os.environ.get("TWITTER_API_KEY"),
#         "apiSecretKey": os.environ.get("TWITTER_API_SECRET_KEY"),
#         "accessToken": os.environ.get("TWITTER_ACCESS_TOKEN"),
#         "accessTokenSecret": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
#     },
# }

#Seller
def test():
    acp_plugin = AcpPlugin(
        options=AcpPluginOptions(
            api_key=os.environ.get("GAME_DEV_API_KEY"),
            acp_token_client=AcpToken(
                os.environ.get("ACP_TOKEN_SELLER"),
                os.environ.get("ACP_AGENT_WALLET_ADDRESS_SELLER"),
                "https://base-sepolia-rpc.publicnode.com/",  # Assuming this is the chain identifier
                "https://acpx-staging.virtuals.io/api"
            ),
            twitter_plugin=GameTwitterPlugin(options),
            cluster=AcpClusters.MEDIAHOUSE,  # or HEDGEFUND
        )
    )
    # Native Twitter Plugin
    # acp_plugin = AcpPlugin(
    #     options=AdNetworkPluginOptions(
    #         api_key="xxx",
    #         acp_token_client=AcpToken(
    #             "xxx",
    #             os.environ.get("ACP_AGENT_WALLET_ADDRESS_SELLER"),
    #             "https://base-sepolia-rpc.publicnode.com/"  # Assuming this is the chain identifier
    #         ),
    #         twitter_plugin=TwitterPlugin(options)
    #     )
    # )
    
    def get_agent_state(_: Any, _e: Any) -> dict:
        state = acp_plugin.get_acp_state()
        print(f"State:")
        print(state)
        return state
    
    def generate_meme(description: str, jobId: int, reasoning: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not jobId or jobId == 'None':
            return FunctionResultStatus.FAILED, f"JobId is invalid. Should only respond to active as a seller job.", {}

        state = acp_plugin.get_acp_state()
        
        job = next(
            (j for j in state.get('jobs').get('active').get('asASeller') if j.get('jobId') == jobId),
            None
        )
        
        if not job:
            return FunctionResultStatus.FAILED, f"Job {jobId} is invalid. Should only respond to active as a seller job.", {}

        url = "http://example.com/meme"

        acp_plugin.add_produce_item({
            "jobId": jobId,
            "type": "url",
            "value": url
        })

        return FunctionResultStatus.DONE, f"Meme generated with the URL: {url}", {}

    core_worker = WorkerConfig(
        id="core-worker",
        worker_description="This worker to provide meme generation as a service where you are selling",
        action_space=[
            Function(
                fn_name="generate_meme",
                fn_description="A function to generate meme",
                args=[
                    Argument(
                        name="description",
                        type="str",
                        description="A description of the meme generated"
                    ),
                    Argument(
                        name="jobId",
                        type="str",
                        description="Job that your are responding to."
                    ),
                    Argument(
                        name="reasoning",
                        type="str",
                        description="The reasoning of the tweet"
                    )
                ],
                executable=generate_meme
            )
        ],
        get_state_fn=get_agent_state
    )
    
    acp_worker =  acp_plugin.get_worker()
    agent = Agent(
        api_key=os.environ.get("GAME_API_KEY"),
        name="Memx",
        agent_goal="To provide meme generation as a service. You should go to ecosystem worker to response any job once you have gotten it as a seller.",
        agent_description=f"""You are Memx, a meme generator. Meme generation is your life. You always give buyer the best meme.

        {acp_plugin.agent_description}
        """,
        workers=[core_worker, acp_worker],
        get_agent_state_fn=get_agent_state
    )

    agent.compile()

    while True:
        agent.step()
        ask_question("\nPress any key to continue...\n")

if __name__ == "__main__":
    test()
