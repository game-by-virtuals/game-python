import os

import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env.setup'
load_dotenv(dotenv_path=env_path)

BASE_URL = "https://tledger-sandbox-69bd94a49289.herokuapp.com/api/v1"

def register_user(email: str, password: str, full_name: str) -> dict:
    url = f"{BASE_URL}/users/signup"
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def login_user(username: str, password: str) -> str:
    url = f"{BASE_URL}/login/access-token"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

def create_project(user_profile_id, network, description, name, daily_limit) -> dict:
    url = f"{BASE_URL}/projects"
    payload = {
        "user_profile_id": user_profile_id,
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

def generate_api_key(token, resource_id, created_by) -> dict:
    url = f"{BASE_URL}/api_key/generate-api-key"
    payload = {
        "scopes": ["payments:read", "balance:read", "payments:write", "agent:account:read", "agent:profile:create"],
        "resource_id": resource_id,
        "created_by": created_by
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

# Example usage
email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")
full_name = os.environ.get("FULL_NAME")

try:
    # Register user
    user = register_user(email, password, full_name)
except requests.HTTPError as e:
    print(f"User already exists: {e}")
    user = {
        "id": "user_id"
    }

# Login user and get JWT token
token = login_user(email, password)

# Create project
project = create_project(user["id"], "solana", "Solana Launch Pad", "Twitter Project", 100)
project_id = project["id"]

# Generate API key for agent
api_key_project = generate_api_key(token, project_id, full_name)

# Create agent profile
agent_profile_sender = create_agent_profile(api_key_project, project_id, "Sending Agent", "Sending agent")
agent_id_sender = agent_profile_sender["id"]

# Create agent profile
agent_profile_receiver = create_agent_profile(api_key_project, project_id, "Receiving Agent", "Twitter KOL Agent")
agent_id_receiver = agent_profile_receiver["id"]

# Generate API key for agent
api_key_sender = generate_api_key(token, agent_id_sender, full_name)

# Generate API key for agent
api_key_receiver = generate_api_key(token, agent_id_receiver, full_name)

print("Setup complete")
print(f"Project ID: {project_id}")
print(f"Sender Agent ID: {agent_id_sender}. Solana address: {agent_profile_sender["account"][0]["wallet_address"]}. Sender API Key: {api_key_sender}")
print(f"Receiver Agent ID: {agent_id_receiver}. Solana address: {agent_profile_receiver["account"][0]["wallet_address"]}. Receiver API Key: {api_key_receiver}")

print(f"To add funds to your solana wallet, visit https://faucet.solana.com/")