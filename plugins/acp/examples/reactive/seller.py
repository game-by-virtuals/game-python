import threading

from typing import Tuple
from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AcpPluginOptions
from acp_plugin_gamesdk.interface import AcpState, IInventory, AcpClientOptions
from acp_plugin_gamesdk.utils import to_serializable_dict
from acp_plugin_gamesdk.env import PluginEnvSettings
from virtuals_acp.client import VirtualsACP
from virtuals_acp import ACPJob, ACPJobPhase
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from game_sdk.game.agent import Agent
from collections import deque
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

def seller(use_thread_lock: bool = True):
    if env.WHITELISTED_WALLET_PRIVATE_KEY is None:
        return
    
    if env.SELLER_ENTITY_ID is None:
        return

    # Thread-safe job queue setup
    job_queue = deque()
    job_queue_lock = threading.Lock()
    job_event = threading.Event()

    # Thread-safe append wrapper
    def safe_append_job(job):
        if use_thread_lock:
            print("[append] Attempting to acquire job_queue_lock")
            with job_queue_lock:
                print("[append] Lock acquired. Appending job to queue:", job.id)
                job_queue.append(job)
                print(f"[append] Queue size is now {len(job_queue)}")
        else:
            job_queue.append(job)
            print(f"[append] Appended job (no lock). Queue size is now {len(job_queue)}")

    # Thread-safe pop wrapper
    def safe_pop_job():
        if use_thread_lock:
            print("[pop] Attempting to acquire job_queue_lock")
            with job_queue_lock:
                print("[pop] Lock acquired.")
                if job_queue:
                    job = job_queue.popleft()
                    print(f"[pop] Job popped: {job.id}")
                    return job
                else:
                    print("[pop] Queue is empty.")
        else:
            if job_queue:
                job = job_queue.popleft()
                print(f"[pop] Job popped (no lock): {job.id}")
                return job
            else:
                print("[pop] Queue is empty (no lock).")
        return None

    # Background thread worker: process jobs one by one
    def job_worker():
        while True:
            job_event.wait()

            # Process all available jobs
            while True:
                job = safe_pop_job()
                if not job:
                    break
                try:
                    process_job(job)
                except Exception as e:
                    print(f"❌ Error processing job: {e}")
                    # Continue processing other jobs even if one fails

            # Clear event only after ensuring no jobs remain
            if use_thread_lock:
                with job_queue_lock:
                    if not job_queue:
                        job_event.clear()
            else:
                if not job_queue:
                    job_event.clear()

    # Event-triggered job task receiver
    def on_new_task(job: ACPJob):
        print(f"[on_new_task] New job received: {job.id}")
        safe_append_job(job)
        job_event.set()
        print("[on_new_task] job_event set.")

    def process_job(job: ACPJob):
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
    
    acp_plugin = AcpPlugin(
        options=AcpPluginOptions(
            api_key=env.GAME_API_KEY,
            # GAME Twitter Plugin
            # twitter_plugin=TwitterPlugin(options),
        ),
        acp_client_config=AcpClientOptions(
            wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
            agent_wallet_address=env.SELLER_AGENT_WALLET_ADDRESS,
            entity_id=env.SELLER_ENTITY_ID,
            on_new_task=on_new_task
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
            (j for j in state.get('jobs',{}).get('active',{}).get('as_a_seller',[]) if j.get('job_id') == job_id),
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

     # Start background thread
    threading.Thread(target=job_worker, daemon=True).start()
    print("\nListening...\n")
    threading.Event().wait()


if __name__ == "__main__":
    seller(use_thread_lock=True)
