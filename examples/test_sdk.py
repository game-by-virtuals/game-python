"""
Test script to verify SDK installation and API key.
"""

import os
import requests
from dotenv import load_dotenv
from game_sdk.game.utils import get_access_token
from game_sdk.game.agent import Agent
from game_sdk.game.exceptions import AuthenticationError

def get_test_state(function_result, current_state):
    """Simple state function for testing."""
    return {"status": "ready"}

def test_connection():
    """Test SDK connection with API key."""
    # Load environment variables from .env file
    load_dotenv()
    
    api_key = os.getenv("GAME_API_KEY")
    if not api_key:
        print("Error: GAME_API_KEY environment variable not found")
        return False

    try:
        print(f"Using API key: {api_key}")
        
        # Test authentication
        token = get_access_token(api_key)
        print("✅ Successfully authenticated with API")
        
        # Test direct agent creation
        data = {
            "data": {
                "name": "Test Agent",
                "description": "A test agent to verify SDK installation",
                "goal": "Verify that the SDK is working correctly"
            }
        }
        
        response = requests.post(
            "https://api.virtuals.io/api/agents",
            json=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"\nDirect API call to create agent:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Create a test agent using SDK
        agent = Agent(
            api_key=api_key,
            name="Test Agent",
            agent_description="A test agent to verify SDK installation",
            agent_goal="Verify that the SDK is working correctly",
            get_agent_state_fn=get_test_state
        )
        print("✅ Successfully created test agent")
        
        return True
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Testing GAME SDK connection...")
    success = test_connection()
    if success:
        print("\n🎉 SDK is working correctly!")
    else:
        print("\n❌ SDK test failed. Please check the error messages above.")
