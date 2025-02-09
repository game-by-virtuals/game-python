import os
from typing import Dict, Any
import requests

class OpacityPlugin:
    """
    Opacity Plugin for verifying AI inference proofs via Opacity
    """
    
    def __init__(self) -> None:
        """Initialize the Opacity plugin"""
        self.id: str = "opacity_plugin"
        self.name: str = "Opacity Plugin"
        self.prover_url = os.environ.get("OPACITY_PROVER_URL")

    def initialize(self):
        """Initialize the plugin"""
        if not self.prover_url:
            raise ValueError("Missing required environment variable: OPACITY_PROVER_URL")

    def verify_proof(self, result: Dict[str, Any]) -> bool:
        """
        Verify a proof
        
        Args:
            result (Dict[str, Any]): The result containing the proof to verify
            
        Returns:
            bool: True if proof is valid, False otherwise
        """
        response = requests.post(
            f"{self.prover_url}/api/verify",
            headers={"Content-Type": "application/json"},
            json=result["proof"]
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to verify proof: {response.text}")
            
        verification = response.json()
        if not verification.get("success"):
            raise Exception("Proof is invalid")
            
        return verification["success"]