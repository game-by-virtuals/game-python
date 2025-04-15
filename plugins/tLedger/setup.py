import requests

BASE_URL = "https://api-sandbox.t54.ai/api/v1"

def create_project(network, description, name, daily_limit) -> dict:
    url = f"{BASE_URL}/projects"
    payload = {
        "network": network,
        "description": description,
        "name": name,
        "daily_limit": daily_limit
    }

    headers = {}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def create_agent_profile(token, project_id, name, description) -> dict:
    url = f"{BASE_URL}/agent_profiles"
    payload = {
        "project_id": project_id,
        "name": name,
        "description": description
    }
    headers = {
        "X-API-Key": token["api_key"],
        "X-API-Secret": token["secret"]
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def generate_api_key(resource_id, created_by) -> dict:
    url = f"{BASE_URL}/api_key/generate-api-key"
    payload = {
        "scopes": ["payments:read", "balance:read", "payments:write", "agent:account:read", "agent:profile:create"],
        "resource_id": resource_id,
        "created_by": created_by
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


# Create project
project = create_project( "solana", "Solana Launch Pad", "Twitter Project", 100)
project_id = project["id"]

# Generate API key for agent
api_key_project = generate_api_key(project_id, "guest@t54.ai")

# Create agent profile
agent_profile_sender = create_agent_profile(api_key_project, project_id, "Sending Agent", "Sending agent")
agent_id_sender = agent_profile_sender["id"]

# Create agent profile
agent_profile_receiver = create_agent_profile(api_key_project, project_id, "Receiving Agent", "Twitter KOL Agent")
agent_id_receiver = agent_profile_receiver["id"]

# Generate API key for agent
api_key_sender = generate_api_key(agent_id_sender, "guest@t54.ai")

# Generate API key for agent
api_key_receiver = generate_api_key(agent_id_receiver, "guest@t54.ai")

print("Setup complete")
print(f"Project ID: {project_id}")
print(f"Sender Agent ID: {agent_id_sender}. Solana address: {agent_profile_sender["account"][0]["wallet_address"]}. Sender API Key: {api_key_sender}")
print(f"Receiver Agent ID: {agent_id_receiver}. Solana address: {agent_profile_receiver["account"][0]["wallet_address"]}. Receiver API Key: {api_key_receiver}")

print(f"To add funds to your solana wallet, visit https://faucet.solana.com/")