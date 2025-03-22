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

def create_project(token, user_profile_id, network, description, name, daily_limit) -> dict:
    url = f"{BASE_URL}/projects"
    payload = {
        "user_profile_id": user_profile_id,
        "network": network,
        "description": description,
        "name": name,
        "daily_limit": daily_limit
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
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
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def generate_api_key(token, agent_id, created_by) -> dict:
    url = f"{BASE_URL}/api_key/generate-api-key"
    payload = {
        "scopes": ["payments:read", "payments:write", "payments:agent:read"],
        "agent_id": agent_id,
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

# Register user
user = register_user(email, password, full_name)

# Login user and get JWT token
token = login_user(email, password)

# Create project
project = create_project(token, user["id"], "solana", "Solana Launch Pad", "Twitter Project", 100)
project_id = project["id"]

# Create agent profile
agent_profile = create_agent_profile(token, project_id, "My Agent", "Twitter KOL Agent")
agent_id = agent_profile["id"]

# Generate API key for agent
api_key = generate_api_key(token, agent_id, full_name)

print("Setup complete")
print(f"Project ID: {project_id}")
print(f"Agent ID: {agent_id}")
print(f"API Key: {api_key}")

print(f"To add funds to your solana wallet, visit https://faucet.solana.com/")