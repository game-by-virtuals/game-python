from typing import Dict, List, Optional, Tuple
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
import requests
import os

DEFAULT_BASE_API_URL = "https://api.together.xyz/v1/images/generations"


class ImageGenPlugin:
    """
    AI Image Generation plugin using Together.ai API.
    
    Requires:
    - Together.ai API key
    
    Example:
        client = ImageGenPlugin(
            api_key="your-together-api-key",
            api_url="https://api.together.xyz/v1/images/generations",
        )

        generate_image_fn = client.get_function("generate_image")
    """
    def __init__(
        self,
        api_key: Optional[str] = os.environ.get("TOGETHER_API_KEY"),
        api_url: Optional[str] = DEFAULT_BASE_API_URL,
    ):
        self.api_key = api_key
        self.api_url = api_url

        # Available client functions
        self._functions: Dict[str, Function] = {
            "generate_image": Function(
                fn_name="generate_image",
                fn_description="Generates AI generated image based on prompt.",
                args=[
                    Argument(
                        name="prompt",
                        description="The prompt for image generation model. Example: A dog in the park",
                        type="string",
                    ),
                    Argument(
                        name="width",
                        description="Width of generated image, up to 1440 px. Default should be 1024 unless other sizes specifically needed.",
                        type="int",
                    ),
                    Argument(
                        name="height",
                        description="Height of generated image, up to 1440 px. Default should be 1024 unless other sizes specifically needed.",
                        type="int",
                    ),
                ],
                hint="This function is used to generate an AI image based on prompt",
                executable=self.generate_image,
            ),
        }

    @property
    def available_functions(self) -> List[str]:
        """Get list of available function names."""
        return list(self._functions.keys())

    def get_function(self, fn_name: str) -> Function:
        """
        Get a specific function by name.

        Args:
            fn_name: Name of the function to retrieve

        Raises:
            ValueError: If function name is not found

        Returns:
            Function object
        """
        if fn_name not in self._functions:
            raise ValueError(
                f"Function '{fn_name}' not found. Available functions: {', '.join(self.available_functions)}"
            )
        return self._functions[fn_name]

    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024, **kwargs) -> str:
        """Generate image based on prompt.

        Returns:
            str URL of image (need to save since temporal)
        """
        # API endpoint for image generation
        url = DEFAULT_BASE_API_URL

        # Prepare headers for the request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Prepare request payload
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell-Free",
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": 1,
            "n": 1,
            "response_format": "url",
        }

        try:
            # Make the API request
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()

            # Extract the image URL from the response
            response_data = response.json()
            image_url = response_data["data"][0]["url"]

            return (
                FunctionResultStatus.DONE,
                f"The generated image is: {image_url}",
                {
                    "prompt": prompt,
                    "image_url": image_url,
                },
            )
        except Exception as e:
            print(f"An error occurred while generating image: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"An error occurred while while generating image: {str(e)}",
                {
                    "prompt": prompt,
                },
            )
