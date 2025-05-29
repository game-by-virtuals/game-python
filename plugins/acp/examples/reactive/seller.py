import os
import threading

from typing import Any,Tuple
from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AcpPluginOptions
from acp_plugin_gamesdk.interface import AcpJobPhasesDesc, AcpState, IInventory, AcpJob
from acp_plugin_gamesdk.acp_token import AcpToken
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from game_sdk.game.agent import Agent
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


# GAME Twitter Plugin options
options = {
    "id": "twitter_plugin",
    "name": "Twitter Plugin",
    "description": "Twitter Plugin for tweet-related functions.",
    "credentials": {
        "gameTwitterAccessToken": os.environ.get("SELLER_AGENT_GAME_TWITTER_ACCESS_TOKEN")
    },
}

# Native Twitter Plugin options
# options = {
#     "id": "twitter_plugin",
#     "name": "Twitter Plugin",
#     "description": "Twitter Plugin for tweet-related functions.",
#     "credentials": {
#         "bearerToken": os.environ.get("SELLER_AGENT_TWITTER_BEARER_TOKEN"),
#         "apiKey": os.environ.get("SELLER_AGENT_TWITTER_API_KEY"),
#         "apiSecretKey": os.environ.get("SELLER_AGENT_TWITTER_API_SECRET_KEY"),
#         "accessToken": os.environ.get("SELLER_AGENT_TWITTER_ACCESS_TOKEN"),
#         "accessTokenSecret": os.environ.get("SELLER_AGENT_TWITTER_ACCESS_TOKEN_SECRET"),
#     },
# }

def seller():
    def on_phase_change(job: AcpJob) -> None:
        out = ""
        out += f"Reacting to job:\n{job}\n\n"
        prompt = ""

        if isinstance(job, dict):
            phase = job.get('phase')
        else:
            phase = job.phase

        out += f"Phase: {phase}\n\n"
        
        if "getAgentByWalletAddress" in job and job["getAgentByWalletAddress"] is not None:
            client_agent = job["getAgentByWalletAddress"](job["clientAddress"])
            print("Client Agent Twitter Handle:", client_agent.twitter_handle)

        if phase == AcpJobPhasesDesc.REQUEST:
            prompt = f"""
            Respond to the following transaction:
            {job}

            decide whether you should accept the job or not.
            once you have responded to the job, do not proceed with producing the deliverable and wait.
            """
        elif phase == AcpJobPhasesDesc.TRANSACTION:
            prompt = f"""
            Respond to the following transaction:
            {job}

            you should produce the deliverable and deliver it to the buyer.

            If no deliverable is provided, you should produce the deliverable and deliver it to the buyer.
            """
        else:
            out += "No need to react to the phase change\n\n"

        if prompt:
            worker = agent.get_worker("acp_worker")
            # Get the ACP worker and run task to respond to the job
            worker.run(prompt)

            out += f"Running task:\n{prompt}\n\n"
            out += "✅ Seller has responded to job.\n"

        print(Panel(out, title="🔁 Reaction", box=box.ROUNDED, title_align="left", border_style="red"))

    acp_plugin = AcpPlugin(
        options=AcpPluginOptions(
            api_key=os.environ.get("GAME_DEV_API_KEY"),
            acp_token_client=AcpToken(
                os.environ.get("WHITELISTED_WALLET_PRIVATE_KEY"),
                os.environ.get("SELLER_AGENT_WALLET_ADDRESS"),
                BASE_SEPOLIA_CONFIG
            ),
            on_phase_change=on_phase_change,
            # GAME Twitter Plugin
            twitter_plugin=GameTwitterPlugin(options)
            # Native Twitter Plugin
            # twitter_plugin=TwitterPlugin(options)
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
            (j for j in state.get('jobs').get('active').get('asASeller') if j.get('jobId') == job_id),
            None
        )

        if not job:
            return FunctionResultStatus.FAILED, f"Job {job_id} is invalid. Should only respond to active as a seller job.", {}

        url = "https://example.com/meme"

        meme = IInventory(
            jobId=job_id,
            type="url",
            value=url,
            clientName=job.get("clientName"),
            providerName=job.get("providerName"),
        )

        acp_plugin.add_produce_item(meme)

        return FunctionResultStatus.DONE, f"Meme generated with the URL: {url}", {}

    generate_meme_function = Function(
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

    acp_worker = acp_plugin.get_worker(
        {
            "functions": [
                acp_plugin.respond_job,
                acp_plugin.deliver_job,
                generate_meme_function
            ]
        }
    )

    agent = Agent(
        api_key=os.environ.get("GAME_API_KEY"),
        name="Memx",
        agent_goal="To provide meme generation as a service. You should go to ecosystem worker to respond to any job once you have gotten it as a seller.",
        agent_description=f"""
        You are Memx, a meme generator. Meme generation is your life. You always give buyer the best meme.

        {acp_plugin.agent_description}
        """,
        workers=[acp_worker],
        get_agent_state_fn=get_agent_state
    )

    agent.compile()

    print("🟢"*40)
    init_state = from_dict(data_class=AcpState, data=agent.agent_state, config=Config(type_hooks={AcpJobPhasesDesc: AcpJobPhasesDesc}))
    print(Panel(f"{init_state}", title="Agent State", box=box.ROUNDED, title_align="left"))
    print("🔴"*40)
    active_jobs = agent.agent_state.get("jobs").get("active").get("asASeller")
    if active_jobs:
        for job in active_jobs:
            on_phase_change(job)
    print("\nListening\n")
    threading.Event().wait()


if __name__ == "__main__":
    seller()
