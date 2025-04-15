import os
from typing import Dict, Any

import requests

from src.game_sdk.game.custom_types import Function, Argument, FunctionResultStatus

BASE_URL = "https://api-sandbox.t54.ai/api/v1/"


class TLedgerPlugin:


    def __init__(
        self,
        api_key: str,
        api_secret: str,
        api_url: str,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.api_secret = api_secret

        # Available client functions
        self.functions: Dict[str, Function] = {
            "create_payment": Function(
                fn_name="create_payment",
                fn_description="Create payment",
                hint="This function is used to get the agent profile details for a given agent",
                executable=self.create_payment,
                args=[
                    Argument(
                        name="request_id",
                        description="Unique ID for requesting the payment to ensure idempotence",
                        type="string",
                    ),
                    Argument(
                        name="receiving_agent_id",
                        description="The Unique ID of the receiving agent.",
                        type="string",
                    ),
                    Argument(
                        name="payment_amount",
                        description="Amount to be paid",
                        type="float",
                    ),
                    Argument(
                        name="settlement_network",
                        description="network used for settlement",
                        type="string",
                    ),
                    Argument(
                        name="currency",
                        description="Currency used in the crypto bridge",
                        type="string",
                    ),
                    Argument(
                        name="conversation_id",
                        description="Conversation ID to correlate the agent conversation",
                        type="string",
                    ),
                ],
            ),
            "get_payment_by_id": Function(
                fn_name="get_payment_by_id",
                fn_description="Get payment",
                hint="This function is used to get the payment by payment id",
                executable=self.get_payment_by_id,
                args=[
                    Argument(
                        name="payment_id",
                        description="Unique ID for the payment",
                        type="string",
                    )
                ],
            ),

            "get_agent_profile_details": Function(
                fn_name="get_agent_profile_details",
                fn_description="Get agent profile details",
                hint="This function is used to get the agent profile details for a given agent",
                executable=self.get_agent_profile_details,
                args=[],
            ),
        }

    def get_tools(self) -> list[Function]:
        # returns the available functions
        return list(self.functions.values())

    def create_payment(self, request_id: str, receiving_agent_id: str, payment_amount: float, settlement_network: str, currency: str, conversation_id: str, **kwargs) -> \
    tuple[FunctionResultStatus, str, dict[str, Any]] | tuple[FunctionResultStatus, str, dict[Any, Any]]:
        """Generate image based on prompt.

        Returns:
            str URL of image (need to save since temporal)
        """
        # API endpoint for image generation
        # Prepare headers for the request
        headers = {
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret,
            "Content-Type": "application/json",
        }

        # Prepare request payload
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell-Free",
            "request_id": request_id,
            "receiving_agent_id": receiving_agent_id,
            "payment_amount": payment_amount,
            "settlement_network": settlement_network,
            "currency": currency,
            "conversation_id": conversation_id,
        }

        try:

            url = self.api_url + "payment"

            # Make the API request
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            # Extract the image URL from the response
            response_data = response.json()

            return (
                FunctionResultStatus.DONE,
                f"The create payment response is: {response_data}",
                {
                    "response": response_data,
                },
            )
        except Exception as e:
            print(f"An error occurred while creating a payment: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"An error occurred while creating a payment: {str(e)}",
                {
                },
            )

    def get_payment_by_id(self, payment_id: str, **kwargs) -> \
            tuple[FunctionResultStatus, str, dict[str, Any]] | tuple[FunctionResultStatus, str, dict[Any, Any]]:
        """Generate image based on prompt.

        Returns:
            str URL of image (need to save since temporal)
        """
        # API endpoint for image generation
        # Prepare headers for the request
        headers = {
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret,
            "Content-Type": "application/json",
        }

        get_url = self.api_url + f"payment/{payment_id}"

        try:
            # Make the API request
            response = requests.get(get_url, headers=headers)
            response.raise_for_status()

            # Extract the image URL from the response
            response_data = response.json()

            return (
                FunctionResultStatus.DONE,
                f"The get payment response is: {response_data}",
                {
                    "response": response_data,
                },
            )
        except Exception as e:
            print(f"An error occurred getting payment: {str(e)}")
            return (
                FunctionResultStatus.FAILED,
                f"An error occurred while while getting payment: {str(e)}",
                {
                    "payment_id": payment_id,
                    "get_url": get_url,
                },
            )

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

