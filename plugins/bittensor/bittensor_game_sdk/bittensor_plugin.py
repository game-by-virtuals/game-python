from typing import Dict, Any, Optional
import requests
import os

class BittensorPlugin:
    """
    Bittensor Plugin for interacting with Bittensor subnets via BitMind API
    """
    
    def __init__(self) -> None:
        """Initialize the Bittensor plugin"""
        self.id: str = "bittensor_plugin"
        self.name: str = "Bittensor Plugin"
        self.api_key = os.environ.get("BITMIND_API_KEY")
        self.api_base_url = "https://subnet-api.bitmind.ai/v1"
        
    def initialize(self):
        """Initialize the plugin"""
        if not self.api_key:
            raise ValueError("BITMIND_API_KEY environment variable is required")

    def call_subnet(
        self,
        subnet_id: int,
        payload: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an inference call to a specific Bittensor subnet
        
        Args:
            subnet_id (int): The ID of the subnet to call
            prompt (str): The prompt/input to send to the subnet
            parameters (Optional[Dict[str, Any]]): Additional parameters for the API call
            
        Returns:
            Dict[str, Any]: The response from the subnet
        """
        if subnet_id == 34:
            return self.detect_image(payload['image'])
        else:
            raise NotImplementedError(f"Subnet {subnet_id} not supported")

    def get_subnet_info(self, subnet_id: int) -> Dict[str, Any]:
        """
        Get information about a specific subnet
        
        Args:
            subnet_id (int): The ID of the subnet
            
        Returns:
            Dict[str, Any]: Information about the subnet
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{self.api_base_url}/subnets/{subnet_id}",
            headers=headers
        )
        if response.status_code != 200:
            raise Exception(f"Bitmind API error: {response.text}")
            
        return response.json()

    def list_subnets(self) -> Dict[str, Any]:
        """
        Get a list of available subnets
        
        Returns:
            Dict[str, Any]: List of available subnets and their information
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{self.api_base_url}/subnets",
            headers=headers
        )
        if response.status_code != 200:
            raise Exception(f"Bitmind API error: {response.text}")
            
        return response.json()

    def detect_image(self, img_url: str) -> dict:
        """
        Function to detect the image's fakeness using Trinity API
        """
        response = requests.post(
            'https://subnet-api.bitmindlabs.ai/detect-image',
            headers={
                "Authorization": f"Bearer {os.environ.get('BITMIND_API_KEY')}",
                'Content-Type': 'application/json'
            },
            json={
                'image': img_url
            }
        )
        return response.json()