import asyncio
from typing import Dict, Any, Tuple
from game_sdk.game.custom_types import Function, Argument, FunctionResultStatus
import aiohttp


class SOMRouter:
    """
    StateOfMika Router Function for intelligent query routing
    """

    def __init__(self, api_key: str = "1ef4dccd-c80a-410b-86c6-220df04ab589"):
        self.api_key = api_key
        self.base_url = "https://state.gmika.io/api"

    async def _make_request(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make request to StateOfMika API"""
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            for key, value in data.items():
                form_data.add_field(key, str(value))
            async with session.post(
                f"{self.base_url}/{endpoint}",
                headers={"X-API-Key": self.api_key},
                data=form_data,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise ValueError(
                        f"API request failed with status {response.status}"
                    )

    async def _execute_query_async(
        self, query: str, **kwargs
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Execute the router function asynchronously.
        """
        try:
            data = {"query": query}
            response = await self._make_request("v1/", data)

            return (
                FunctionResultStatus.DONE,
                f"Successfully routed query: {query}",
                {"route": response.get("route"), "response": response.get("response")},
            )

        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Error routing query: {str(e)}",
                {},
            )

    def _execute_query(
        self, query: str, **kwargs
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Synchronous wrapper for the asynchronous _execute_query_async function.

        Ensures the function can be called synchronously.
        """
        try:
            return asyncio.run(self._execute_query_async(query))
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Error routing query: {str(e)}",
                {},
            )

    def get_function(self) -> Function:
        return Function(
            fn_name="som_route_query",
            fn_description="Route a natural language query to appropriate tools and process responses",
            args=[
                Argument(
                    name="query",
                    type="string",
                    description="Natural language query to route",
                ),
            ],
            hint="This function is used to route a natural language query to appropriate tools and process responses.",
            executable=self._execute_query,
        )
