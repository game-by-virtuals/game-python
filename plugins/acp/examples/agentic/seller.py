import os

from dacite import from_dict
from dacite.config import Config
from rich import print, box
from rich.panel import Panel
from typing import Tuple
from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AcpPluginOptions
from virtuals_acp.client import VirtualsACP
from acp_plugin_gamesdk.env import PluginEnvSettings
from acp_plugin_gamesdk.interface import AcpState, AcpJobPhasesDesc, IInventory
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from game_sdk.game.agent import Agent, WorkerConfig
from dotenv import load_dotenv

# GAME Twitter Plugin import
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

# Native Twitter Plugin import
# from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

load_dotenv(override=True)

env = PluginEnvSettings()


# GAME Twitter Plugin options
options = {
    "id": "twitter_plugin",
    "name": "Twitter Plugin",
    "description": "Twitter Plugin for tweet-related functions.",
    "credentials": {
        "game_twitter_access_token": env.SELLER_AGENT_GAME_TWITTER_ACCESS_TOKEN
    },
}

# Native Twitter Plugin options
# options = {
#     "id": "twitter_plugin",
#     "name": "Twitter Plugin",
#     "description": "Twitter Plugin for tweet-related functions.",
#     "credentials": {
#         "bearerToken": env.SELLER_AGENT_TWITTER_BEARER_TOKEN,
#         "apiKey": env.SELLER_AGENT_TWITTER_API_KEY,
#         "apiSecretKey": env.SELLER_AGENT_TWITTER_API_SECRET_KEY,
#         "accessToken": env.SELLER_AGENT_TWITTER_ACCESS_TOKEN,
#         "accessTokenSecret": env.SELLER_AGENT_TWITTER_ACCESS_TOKEN_SECRET,
#     },
# }

def seller():
    acp_plugin = AcpPlugin(
        options=AcpPluginOptions(
            api_key=env.GAME_API_KEY,
            acp_client=VirtualsACP(
                wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
                agent_wallet_address=env.SELLER_AGENT_WALLET_ADDRESS,
                entity_id=env.SELLER_ENTITY_ID
            ),       
             twitter_plugin=TwitterPlugin(options)
        )
    )

    def get_agent_state(_: None, _e: None) -> dict:
        state = acp_plugin.get_acp_state()
        return state

    def generate_meme(description: str, job_id: int, reasoning: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not job_id or job_id == 'None':
            return FunctionResultStatus.FAILED, f"job_id is invalid. Should only respond to active as a seller job.", {}

        state = acp_plugin.get_acp_state()

        job = next(
            (j for j in state.get('jobs',{}).get('active').get('as_a_seller') if j.get('job_id') == job_id),
            None
        )

        if not job:
            return FunctionResultStatus.FAILED, f"Job {job_id} is invalid. Should only respond to active as a seller job.", {}

        url = "https://example.com/meme"

        meme = IInventory(
            type="url",
            value=url,
            job_id=job_id,
            client_name=job.get("client_name"),
            provider_name=job.get("provider_name"),
        )

        acp_plugin.add_produce_item(meme)

        return FunctionResultStatus.DONE, f"Meme generated with the URL: {url}, next step is to deliver it to the client.", {}

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
                        name="job_id",
                        type="integer",
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

    acp_worker = acp_plugin.get_worker(
        {
            "functions": [
                acp_plugin.respond_job,
                acp_plugin.deliver_job
            ]
        }
    )

    agent = Agent(
        api_key=env.GAME_API_KEY,
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
        print("🟢"*40)
        agent.step()
        state = AcpState.model_validate(agent.agent_state)
        print(Panel(f"{state}", title="Agent State", box=box.ROUNDED, title_align="left"))
        print("🔴"*40)
        input("\nPress any key to continue...\n")

if __name__ == "__main__":
    seller()
