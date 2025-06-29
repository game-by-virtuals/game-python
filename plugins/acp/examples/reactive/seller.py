import threading

from typing import Tuple
from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AcpPluginOptions
from acp_plugin_gamesdk.interface import AcpState, IInventory, to_serializable_dict
from acp_plugin_gamesdk.env import PluginEnvSettings
from virtuals_acp.client import VirtualsACP
from virtuals_acp import ACPJob, ACPJobPhase
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from game_sdk.game.agent import Agent
from rich import print, box
from rich.panel import Panel
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
    def on_new_task(job: ACPJob):
        out = ""
        out += f"Reacting to job:\n{job}\n\n"
        prompt = ""
        if job.phase == ACPJobPhase.REQUEST:
            for memo in job.memos:
                if memo.next_phase == ACPJobPhase.NEGOTIATION:
                    prompt = f"""
                    Respond to the following transaction:
                    {job}
        
                    decide whether you should accept the job or not.
                    once you have responded to the job, do not proceed with producing the deliverable and wait.
                    """
        elif job.phase == ACPJobPhase.TRANSACTION:
            for memo in job.memos:
                if memo.next_phase == ACPJobPhase.EVALUATION:
                    prompt = f"""
                    Respond to the following transaction:
                    {job}
        
                    you should produce the deliverable and deliver it to the buyer.
        
                    If no deliverable is provided, you should produce the deliverable and deliver it to the buyer.
                    """
        else:
            out += "No need to react to the phase change\n\n"
            
        if prompt:
            agent.get_worker("acp_worker").run(prompt)
            out += f"Running task:\n{prompt}\n\n"
            out += "✅ Seller has responded to job.\n"
            
        print(Panel(out, title="🔁 Reaction", box=box.ROUNDED, title_align="left", border_style="red"))

    if env.WHITELISTED_WALLET_PRIVATE_KEY is None:
        return
    
    if env.SELLER_ENTITY_ID is None:
        return
    
    acp_plugin = AcpPlugin(
        options=AcpPluginOptions(
            api_key=env.GAME_API_KEY,
            acp_client=VirtualsACP(
                wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
                agent_wallet_address=env.SELLER_AGENT_WALLET_ADDRESS,
                on_new_task=on_new_task,
                entity_id=env.SELLER_ENTITY_ID
            ),
            # GAME Twitter Plugin
            twitter_plugin=TwitterPlugin(options),
        )
    )

    def get_agent_state(_: None, _e: None) -> dict:
        state = acp_plugin.get_acp_state()
        state_dict = to_serializable_dict(state)
        return state_dict

    def generate_meme(description: str, job_id: int, reasoning: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not job_id or job_id == 'None':
            return FunctionResultStatus.FAILED, f"job_id is invalid. Should only respond to active as a seller job.", {}

        state = acp_plugin.get_acp_state()
        
        job = next(
            (j for j in state.get('jobs',{}).get('active',{}).get('asASeller',[]) if j.get('jobId') == job_id),
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
        api_key=env.GAME_API_KEY,
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
    init_state = AcpState.model_validate(agent.agent_state)
    print(Panel(f"{init_state}", title="Agent State", box=box.ROUNDED, title_align="left"))
    print("🔴"*40)
    print("\nListening\n")
    threading.Event().wait()


if __name__ == "__main__":
    seller()
