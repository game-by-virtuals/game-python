from copy import deepcopy
from pprint import pprint
from dotenv import load_dotenv
from typing import List, Dict, Any

from acp_plugin_gamesdk.acp_plugin import AcpPlugin, AcpPluginOptions
from acp_plugin_gamesdk.utils import to_serializable_dict
from acp_plugin_gamesdk.env import PluginEnvSettings
from virtuals_acp.client import VirtualsACP
from virtuals_acp.configs import BASE_MAINNET_CONFIG

load_dotenv(override=True)
env = PluginEnvSettings()

acp_plugin = AcpPlugin(
    options=AcpPluginOptions(
        api_key=env.GAME_DEV_API_KEY,
        acp_client=VirtualsACP(
            wallet_private_key=env.WHITELISTED_WALLET_PRIVATE_KEY,
            agent_wallet_address=env.SELLER_AGENT_WALLET_ADDRESS,
            config=BASE_MAINNET_CONFIG,
            entity_id=env.SELLER_ENTITY_ID
        )
    )
)

def get_agent_state(_: None, _e: None) -> dict:
    state = acp_plugin.get_acp_state()
    state_dict = to_serializable_dict(state)
    return state_dict

def delete_old_items(items: list, keep: int, label: str) -> list:
    if len(items) <= keep:
        return items
    sorted_items = sorted(items, key=lambda x: x.get("job_id", 0), reverse=True)
    deleted_count = len(items) - keep
    print(f"Deleted {deleted_count} {label}, keeping {keep} most recent")
    return sorted_items[:keep]

def delete_completed_jobs(state: Dict, keep_most_recent: int = 5) -> Dict:
    filtered_state = deepcopy(state)
    filtered_state["jobs"]["completed"] = delete_old_items(
        filtered_state["jobs"]["completed"], keep_most_recent, "completed jobs"
    )
    return filtered_state


def delete_cancelled_jobs(state: Dict, keep_most_recent: int = 5) -> Dict:
    filtered_state = deepcopy(state)
    filtered_state["jobs"]["cancelled"] = delete_old_items(
        filtered_state["jobs"]["cancelled"], keep_most_recent, "cancelled jobs"
    )
    return filtered_state

def delete_old_jobs(state: Dict, keep_completed: int = 5, keep_cancelled: int = 5) -> Dict:
    state = delete_completed_jobs(state, keep_completed)
    return delete_cancelled_jobs(state, keep_cancelled)

def delete_acquired_inventory(state: Dict, keep_most_recent: int = 5) -> Dict:
    filtered_state = deepcopy(state)
    filtered_state["inventory"]["acquired"] = delete_old_items(
        filtered_state["inventory"]["acquired"], keep_most_recent, "acquired inventory"
    )
    return filtered_state

def delete_produced_inventory(state: Dict, keep_most_recent: int = 5) -> Dict:
    filtered_state = deepcopy(state)
    filtered_state["inventory"]["produced"] = delete_old_items(
        filtered_state["inventory"]["produced"], keep_most_recent, "produced inventory"
    )
    return filtered_state

def delete_old_inventory(state: Dict, keep_acquired: int = 5, keep_produced: int = 5) -> Dict:
    state = delete_acquired_inventory(state, keep_acquired)
    return delete_produced_inventory(state, keep_produced)

def filter_out_job_ids(state: Dict, job_ids_to_ignore: List[int]) -> Dict:
    """
    Filters out jobs with specific job IDs from active job lists.

    Args:
        state (Dict): The agent state dictionary.
        job_ids_to_ignore (List[int]): List of job IDs to exclude.

    Returns:
        Dict: A new state dictionary with specified job IDs removed.
    """
    if not job_ids_to_ignore:
        return state

    filtered_state = state.copy()
    jobs = filtered_state.get("jobs", {})
    active = jobs.get("active", {})

    if "as_a_buyer" in active:
        active["as_a_buyer"] = [
            job for job in active["as_a_buyer"]
            if job.get("job_id") not in job_ids_to_ignore
        ]

    if "as_a_seller" in active:
        active["as_a_seller"] = [
            job for job in active["as_a_seller"]
            if job.get("job_id") not in job_ids_to_ignore
        ]

    filtered_state["jobs"]["active"] = active
    return filtered_state

def reduce_agent_state(
    state: Dict,
    keep_completed_jobs: int = 5,
    keep_cancelled_jobs: int = 5,
    keep_acquired_inventory: int = 5,
    keep_produced_inventory: int = 5,
    job_ids_to_ignore: List[int] = [],
    agent_addresses_to_ignore: List[str] = [],
) -> Dict:
     # Step 1: Filter specific job IDs
    if job_ids_to_ignore:
        state = filter_out_job_ids(state, job_ids_to_ignore)

    # Step 2: Filter jobs from any ignored agent address
    if agent_addresses_to_ignore:
        active_jobs = state.get("jobs", {}).get("active", {})
        all_active = active_jobs.get("as_a_buyer", []) + active_jobs.get("as_a_seller", [])
        matching_ids = [
            job["job_id"]
            for job in all_active
            if job.get("provider_address", "") in agent_addresses_to_ignore
        ]
        if matching_ids:
            print(f"Removing {len(matching_ids)} active jobs from ignored agents: {', '.join(map(str, matching_ids))}")
            state = filter_out_job_ids(state, matching_ids)
    
    # Step 3: Clean up historical data
    state = delete_old_jobs(state, keep_completed_jobs, keep_cancelled_jobs)
    state = delete_old_inventory(state, keep_acquired_inventory, keep_produced_inventory)
    return state

if __name__ == "__main__":
    # Test example
    def get_agent_state(_: None, _e: None) -> dict:
        state = acp_plugin.get_acp_state()
        state_dict = to_serializable_dict(state)
        return reduce_agent_state(
            state_dict,
            keep_completed_jobs=1,
            keep_cancelled_jobs=1,
            keep_acquired_inventory=1,
            keep_produced_inventory=1,
            job_ids_to_ignore=[6294, 6293, 6269],
            agent_addresses_to_ignore=["0x408AE36F884Ef37aAFBA7C55aE1c9BB9c2753995"],
        )
    reduced_agent_state = get_agent_state(None, None)
    print("\n🧹 Cleaned State:")
    pprint(reduced_agent_state)
