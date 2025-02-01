import asyncio
from typing import Dict, Any, Tuple
from game_sdk.game.custom_types import Function, Argument, FunctionResultStatus
import aiohttp

class SOMRouterFunction(Function):
    """
    StateOfMika Router Function for intelligent query routing
    """
    def __init__(self, api_key: str = ""):
        super().__init__(
            fn_name="som_route_query",
            fn_description="Route a natural language query to appropriate tools and process responses",
            args=[
                Argument(
                    name="query",
                    type="string",
                    description="Natural language query to route"
                ),
            ]
        )
        self.api_key = api_key
        self.base_url = "https://state.gmika.io/api"
        self.executable = self._sync_executable

    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
                    error_msg = await response.text()
                    raise ValueError(f"API request failed: {error_msg}")

    async def _execute_query(self, query: str, **kwargs) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
        """
        Execute the router function
        
        Args:
            query: Natural language query
            context: Optional context information
            
        Returns:
            Tuple of (status, message, response data)
        """
        try:
            # Prepare request data
            data = {
                "query": query,
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

    def _sync_executable(self, **kwargs) -> Tuple[FunctionResultStatus, str, Dict[str, Any]]:
            """
            Synchronous wrapper for the asynchronous executable
            """
            query = kwargs.get("query", "")

            # Use `asyncio.run` to execute the async function in a blocking manner
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an existing event loop (e.g., in a Jupyter notebook), use `asyncio.ensure_future`
                    result = asyncio.ensure_future(self._execute_query(query))
                    return loop.run_until_complete(result)
                else:
                    return asyncio.run(self._execute_query(query))
            except Exception as e:
                return (
                    FunctionResultStatus.FAILED,
                    f"Error executing query synchronously: {str(e)}",
                    {}
                )
