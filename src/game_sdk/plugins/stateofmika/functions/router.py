from typing import Tuple, Dict, Any, Optional
from game_sdk.game.custom_types import Function, Argument, FunctionResult, FunctionResultStatus
import aiohttp
import json

class SOMRouterFunction(Function):
    """
    StateOfMika Router Function for intelligent query routing
    """
    def __init__(self, api_key: str):
        super().__init__(
            fn_name="som_route_query",
            fn_description="Route a natural language query to appropriate tools and process responses",
            args=[
                Argument(
                    name="query",
                    type="string",
                    description="Natural language query to route"
                ),
                Argument(
                    name="instructions",
                    type="string",
                    description="Optional post-processing instructions",
                    optional=True
                )
            ]
        )
        self.api_key = api_key
        self.base_url = "https://som.gmika.io/api"

    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to StateOfMika API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/{endpoint}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = await response.text()
                    raise ValueError(f"API request failed: {error_msg}")

    async def execute(
        self, 
        query: str,
        instructions: Optional[str] = None,
    ) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Execute the router function
        
        Args:
            query: Natural language query
            instructions: Optional post-processing instructions
            context: Optional context information
            
        Returns:
            Tuple of (status, message, response data)
        """
        try:
            # Prepare request data
            data = {
                "query": query,
                "instructions": instructions
            }

            # Make API request
            response = await self._make_request("v1/", data)

            return (
                FunctionResultStatus.DONE,
                f"Successfully routed query: {query}",
                {
                    "route": response.get("route"),
                    "response": response.get("response")
                }
            )

        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"Error routing query: {str(e)}",
                {}
            )