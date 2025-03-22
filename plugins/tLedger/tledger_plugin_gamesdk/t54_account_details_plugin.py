import os
from typing import Dict, Any

import requests

from src.game_sdk.game.custom_types import Function, Argument, FunctionResultStatus

BASE_URL = "https://tledger-sandbox-69bd94a49289.herokuapp.com/api/v1/"

class T54AccountDetailsPlugin:


    def __init__(
        self,
        api_key: str = os.environ.get("TLEDGER_API_KEY"),
        api_secret: str = os.environ.get("TLEDGER_API_SECRET"),
        api_url: str = BASE_URL,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.api_secret = api_secret

        # Available client functions
        self.functions: Dict[str, Function] = {
            "get_agent_profile_details": Function(
                fn_name="get_agent_profile_details",
                fn_description="Get agent profile details",
                hint="This function is used to get the agent profile details for a given agent",
                executable=self.get_agent_profile_details,
                args=[],
            ),
        }

    def get_agent_profile_details(self, **kwargs) -> tuple[FunctionResultStatus, str, dict[str, str]] | tuple[
        FunctionResultStatus, str, dict[str, Any]]:
        """ Get agent profile details for a given agent

        Returns:

        """

        # Prepare headers for the request
        headers = {
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret,
            "Content-Type": "application/json",
        }

        try:

            url = f"{self.api_url}agent_details"

            # Make the API request
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Extract the image URL from the response
            response_data = response.json()
            agent_profile_details = response_data

            return (
                FunctionResultStatus.DONE,
                f"The agent details are: {agent_profile_details}",
                {
                    "agent_details": agent_profile_details,
                },
            )
        except Exception as e:
            print(f"An error occurred while getting the agent details: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"An error occurred while getting the agent details: {str(e)}",
                {
                    "tledger_url": url,
                },
            )

