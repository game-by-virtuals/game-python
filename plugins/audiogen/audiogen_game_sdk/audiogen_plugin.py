from typing import Dict, List, Optional, Tuple
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
import requests

DEFAULT_BASE_API_URL = "https://api.together.ai/v1/audio/generations"
DEFAULT_API_KEY = "UP-17f415babba7482cb4b446a1"


class AudioGenPlugin:
    """
    AI Audio Generation plugin.

    Example:
        client = AudioGenPlugin(
            api_key=os.environ.get("TOGETHER_API_KEY"),
            api_url=os.environ.get("https://api.together.ai/v1/audio/generations"),
        )

        generate_audio_fn = client.get_function("generate_audio")
    """

    def __init__(
        self,
        api_key: Optional[str] = DEFAULT_API_KEY,
        api_url: Optional[str] = DEFAULT_BASE_API_URL,
    ):
        self.api_key = api_key
        self.api_url = api_url

        # Available client functions
        self._functions: Dict[str, Function] = {
            "generate_audio": Function(
                fn_name="generate_audio",
                fn_description="Generates text to speech",
                args=[
                    Argument(
                        name="text",
                        description="The text for audio generation model. Example: Upbeat electronic music with piano",
                        type="string",
                    ),
                    Argument(
                        name="voice",
                        description="Voice, can only be EXACTLY one of 'german conversational woman', 'nonfiction man', 'friendly sidekick', 'french conversational lady', 'french narrator lady', 'german reporter woman', 'indian lady', 'british reading lady', 'british narration lady', 'japanese children book', 'japanese woman conversational', 'japanese male conversational', 'reading lady', 'newsman', 'child', 'meditation lady', 'maria', 'newslady', 'calm lady', 'helpful woman', 'mexican woman', 'korean narrator woman', 'russian calm lady', 'russian narrator man 1', 'russian narrator man 2', 'russian narrator woman', 'hinglish speaking lady', 'italian narrator woman', 'polish narrator woman', 'chinese female conversational', 'pilot over intercom', 'chinese commercial man', 'french narrator man', 'spanish narrator man', 'reading man', 'new york man', 'friendly french man', 'barbershop man', 'indian man', 'australian customer support man', 'friendly australian man', 'wise man', 'friendly reading man', 'customer support man', 'dutch confident man', 'dutch man', 'hindi reporter man', 'italian calm man', 'italian narrator man', 'swedish narrator man', 'polish confident man', 'spanish-speaking storyteller man', 'kentucky woman', 'chinese commercial woman', 'middle eastern woman', 'hindi narrator woman', 'sarah', 'sarah curious', 'laidback woman', 'reflective woman', 'helpful french lady', 'pleasant brazilian lady', 'customer support lady', 'british lady', 'wise lady', 'australian narrator lady', 'indian customer support lady', 'swedish calm lady', 'spanish narrator lady', 'salesman', 'yogaman', 'movieman', 'wizardman', 'australian woman', 'korean calm woman', 'friendly german man', 'announcer man', 'wise guide man', 'midwestern man', 'kentucky man', 'brazilian young man', 'chinese call center man', 'german reporter man', 'confident british man', 'southern man', 'classy british man', 'polite man', 'mexican man', 'korean narrator man', 'turkish narrator man', 'turkish calm man', 'hindi calm man', 'hindi narrator man', 'polish narrator man', 'polish young man', 'alabama male', 'australian male', 'anime girl', 'japanese man book', 'sweet lady', 'commercial lady', 'teacher lady', 'princess', 'commercial man', 'asmr lady', 'professional woman', 'tutorial man', 'calm french woman', 'new york woman', 'spanish-speaking lady', 'midwestern woman', 'sportsman', 'storyteller lady', 'spanish-speaking man', 'doctor mischief', 'spanish-speaking reporter man', 'young spanish-speaking woman', 'the merchant', 'stern french man', 'madame mischief', 'german storyteller man', 'female nurse', 'german conversation man', 'friendly brazilian man', 'german woman', 'southern woman', 'british customer support lady', 'chinese woman narrator', 'pleasant man', 'california girl', 'john', 'anna'",
                        type="string",
                    ),
                ],
                hint="This function is used to generate text to speech",
                executable=self.generate_audio,
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

    def generate_audio(
        self,
        text: str,
        voice: str = "chinese commercial man",
        **kwargs,
    ) -> str:
        """Generate text to speech based on text and voice selection.

        Returns:
            str URL of audio (need to save since temporal)
        """

        # Prepare headers for the request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Prepare request payload
        payload = {
            "input": text,
            "voice": voice,
            "response_format": "raw",
            "sample_rate": 44100,
            "stream": False,
            "model": "cartesia/sonic",
        }

        try:
            # Make the API request
            response = requests.post(self.api_url, headers=headers, json=payload)

            file_name=str(hash(input))+".wav"
            with open(file_name, "wb") as f:
                    f.write(response.content)

            return (
                FunctionResultStatus.DONE,
                f"The generated audio is: {file_name}",
                {
                    "text": text,
                    "path": file_name,
                },
            )
        except Exception as e:
            print(f"An error occurred while generating audio: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"An error occurred while generating audio: {str(e)}",
                {
                    "text": text,
                    "voice": voice,
                },
            )
