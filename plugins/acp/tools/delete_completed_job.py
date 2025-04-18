import os
from acp_plugin_gamesdk.acp_plugin import AcpToken, AcpPlugin, AcpPluginOptions

def delete_completed_job() -> None:
    """Delete completed job for all configured ACP tokens."""
    try:
        api_key = os.environ.get("GAME_DEV_API_KEY")
        acp_token = os.environ.get("ACP_TOKEN_BUYER")
        agent_wallet_address = os.environ.get("ACP_AGENT_WALLET_ADDRESS_BUYER")
        print(f"Deleting completed job for token: {acp_token}, wallet address: {agent_wallet_address}")
        acp_plugin = AcpPlugin(
            options=AcpPluginOptions(
                api_key=api_key,
                    acp_token_client=AcpToken(
                        acp_token,
                        agent_wallet_address,
                        "https://base-sepolia-rpc.publicnode.com/"
                    )
                )
            )
        state = acp_plugin.get_acp_state()
        print(f"Completed jobs: {state.get('jobs').get('completed',[])}")
        
        # Prompt user to input the job ID they want to delete
        job_id = input("Enter the job ID you want to delete: ")
        
        acp_plugin.delete_completed_job(job_id)
        print(f"Successfully deleted completed job for token: {acp_token}")
        exit()
    except Exception as e:
        print(f"Failed to delete completed job: {e}")


if __name__ == "__main__":
    delete_completed_job()
