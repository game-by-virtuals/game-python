import os

from typing import Tuple
from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from acp_plugin_gamesdk.interface import AcpJob, IDeliverable, AcpJobPhasesDesc,AcpState
from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AcpPluginOptions
from acp_plugin_gamesdk.acp_token import AcpToken
from dacite import from_dict
from dacite.config import Config
from acp_plugin_gamesdk.configs import BASE_SEPOLIA_CONFIG
from rich import print, box
from rich.panel import Panel
from dotenv import load_dotenv

# GAME Twitter Plugin import
from twitter_plugin_gamesdk.game_twitter_plugin import GameTwitterPlugin

# Native Twitter Plugin import
# from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

load_dotenv()


def on_evaluate(deliverable: IDeliverable) -> Tuple[bool, str]:
    print(f"Evaluating deliverable: {deliverable}")
    return True, "Default evaluation"

# GAME Twitter Plugin options
options = {
    "id": "twitter_plugin",
    "name": "Twitter Plugin",
    "description": "Twitter Plugin for tweet-related functions.",
    "credentials": {
        "gameTwitterAccessToken": os.environ.get("BUYER_AGENT_GAME_TWITTER_ACCESS_TOKEN")
    },
}

# Native Twitter Plugin options
# options = {
#     "id": "twitter_plugin",
#     "name": "Twitter Plugin",
#     "description": "Twitter Plugin for tweet-related functions.",
#     "credentials": {
#         "bearerToken": os.environ.get("BUYER_AGENT_TWITTER_BEARER_TOKEN"),
#         "apiKey": os.environ.get("BUYER_AGENT_TWITTER_API_KEY"),
#         "apiSecretKey": os.environ.get("BUYER_AGENT_TWITTER_API_SECRET_KEY"),
#         "accessToken": os.environ.get("BUYER_AGENT_TWITTER_ACCESS_TOKEN"),
#         "accessTokenSecret": os.environ.get("BUYER_AGENT_TWITTER_ACCESS_TOKEN_SECRET"),
#     },
# }

def buyer():
    # upon phase change, the buyer agent will respond to the transaction
    def on_phase_change(job: AcpJob) -> None:
        if job.phase != AcpJobPhasesDesc.REJECTED:
            print(f"Job phase is rejected.")
            return
        
        out = ""
        out += f"Buyer agent is reacting to job:\n{job}\n\n"
        
        if "getAgentByWalletAddress" in job and job["getAgentByWalletAddress"] is not None:
            provider_agent = job["getAgentByWalletAddress"](job["providerAddress"])
            print("Provider Agent Twitter Handle:", provider_agent.twitter_handle)
        
        worker = buyer_agent.get_worker("acp_worker")
        # Get the ACP worker and run task to respond to the job
        worker.run(
            f"Respond to the following transaction: {job}",
        )

        out += "Buyer agent has responded to the job\n"
        print(Panel(out, title="🔁 Reaction", box=box.ROUNDED, title_align="left", border_style="red"))

    acp_plugin = AcpPlugin(
        options=AcpPluginOptions(
            api_key=os.environ.get("GAME_DEV_API_KEY"),
            acp_token_client=AcpToken(
                os.environ.get("WHITELISTED_WALLET_PRIVATE_KEY"),
                os.environ.get("BUYER_AGENT_WALLET_ADDRESS"),
                BASE_SEPOLIA_CONFIG
            ),
            on_evaluate=on_evaluate,
            on_phase_change=on_phase_change,
            # GAME Twitter Plugin
            twitter_plugin=GameTwitterPlugin(options),
            # Native Twitter Plugin
            # twitter_plugin=TwitterPlugin(options),
        )
    )

    def get_agent_state(_: None, _e: None) -> dict:
        state = acp_plugin.get_acp_state()
        return state

    def post_tweet(content: str, reasoning: str) -> Tuple[FunctionResultStatus, str, dict]:
        if acp_plugin.twitter_plugin is not None:
            post_tweet_fn = acp_plugin.twitter_plugin.get_function('post_tweet')
            post_tweet_fn(content)
            return FunctionResultStatus.DONE, "Tweet has been posted", {}

        return FunctionResultStatus.FAILED, "Twitter plugin is not initialized", {}

    core_worker = WorkerConfig(
        id="core-worker",
        worker_description="This worker is to post tweet",
        action_space=[
            Function(
                fn_name="post_tweet",
                fn_description="This function is to post tweet",
                args=[
                    Argument(
                        name="content",
                        type="string",
                        description="The content of the tweet"
                    ),
                    Argument(
                        name="reasoning",
                        type="string",
                        description="The reasoning of the tweet"
                    )
                ],
                executable=post_tweet
            )
        ],
        get_state_fn=get_agent_state
    )

    acp_worker = acp_plugin.get_worker(
        {
            "functions": [
                acp_plugin.search_agents_functions,
                acp_plugin.initiate_job
            ]
        }
    )

    agent = Agent(
        api_key=os.environ.get("GAME_API_KEY"),
        name="Virtuals",
        agent_goal="Finding the best meme to do tweet posting",
        agent_description=f"""
        Agent that gain market traction by posting meme. Your interest are in cats and AI. 
        You can head to acp to look for agents to help you generating meme.
        Do not look for a relevant validator to validate the deliverable.

        {acp_plugin.agent_description}
        """,
        workers=[core_worker, acp_worker],
        get_agent_state_fn=get_agent_state
    )

    # Buyer agent is meant to handle payments
    buyer_worker = acp_plugin.get_worker(
        {
            "functions": [
                acp_plugin.pay_job
            ]
        }
    )

    buyer_agent = Agent(
        api_key=os.environ.get("GAME_API_KEY"),
        name="Buyer",
        agent_goal="Perform and complete transaction with seller",
        agent_description=f"""
        Agent that gain market traction by posting meme. Your interest are in cats and AI. 
        You can head to acp to look for agents to help you generating meme.
        Do not look for a relevant validator to validate the deliverable.

        {acp_plugin.agent_description}
        """,
        workers=[buyer_worker],
        get_agent_state_fn=get_agent_state
    )

    buyer_agent.compile()
    agent.compile()

    while True:
        print("🟢"*40)
        init_state = from_dict(data_class=AcpState, data=agent.agent_state, config=Config(type_hooks={AcpJobPhasesDesc: AcpJobPhasesDesc}))
        print(Panel(f"{init_state}", title="Initial Agent State", box=box.ROUNDED, title_align="left"))
        agent.step()
        end_state = from_dict(data_class=AcpState, data=agent.agent_state, config=Config(type_hooks={AcpJobPhasesDesc: AcpJobPhasesDesc}))
        print(Panel(f"{end_state}", title="End Agent State", box=box.ROUNDED, title_align="left"))
        print("🔴"*40)
        input("\nPress any key to continue...\n")

if __name__ == "__main__":
    buyer()
