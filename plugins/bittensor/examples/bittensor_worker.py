from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import (
    Function, 
    Argument, 
    FunctionResult, 
    FunctionResultStatus
)
from typing import Dict
import os
from dotenv import load_dotenv
from bittensor_game_sdk.bittensor_plugin import BittensorPlugin

class BittensorImageWorker:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.game_api_key = os.environ.get("GAME_API_KEY")
        self.bittensor_plugin = BittensorPlugin()
        self.worker = self._create_worker()

    def _get_state(self, function_result: FunctionResult, current_state: dict) -> dict:
        """Simple state management"""
        return {}

    def detect_image(self, image_url: str) -> tuple:
        """
        Detect if an image is AI-generated using Bittensor subnet
        """
        try:
            # Validate image URL
            if not image_url.startswith(('http://', 'https://')):
                return FunctionResultStatus.FAILED, "Invalid image URL format", {}

            print(f"Processing image: {image_url}")
            result = self.bittensor_plugin.call_subnet(34, {"image": image_url})
            
            # Check for error response
            if result.get('statusCode') in (400, 500):
                return FunctionResultStatus.FAILED, f"API Error: {result.get('message')}", result
            
            is_ai = result.get('isAI', False)
            confidence = result.get('confidence', 0)
            
            print(f"AI Generated: {is_ai}")
            print(f"Confidence: {confidence}%")
            
            return FunctionResultStatus.DONE, "Image detection successful", result
        except Exception as e:
            print(f"Error detecting image: {e}")
            return FunctionResultStatus.FAILED, f"Error: {str(e)}", {}

    def _create_worker(self) -> Worker:
        """Create worker with image detection capability"""
        return Worker(
            api_key=self.game_api_key,
            description="Worker for detecting AI-generated images using Bittensor",
            instruction="Analyze images to determine if they are AI-generated",
            get_state_fn=self._get_state,
            action_space=[
                Function(
                    fn_name="detect_image",
                    fn_description="Detect if an image is AI-generated",
                    args=[
                        Argument(
                            name="image_url",
                            type="string",
                            description="URL of the image to analyze"
                        )
                    ],
                    executable=self.detect_image
                )
            ]
        )

    def run(self, image_url: str):
        """Run the worker on a single image"""
        self.worker.run(f"Analyze image: {image_url}")

def main():
    # Example usage
    worker = BittensorImageWorker()
    
    # Test with a real, accessible image URL
    test_image = "https://pbs.twimg.com/media/GiOPIuYWcAA3moW.jpg"  # Replace with your test image
    worker.run(test_image)

if __name__ == "__main__":
    main()
