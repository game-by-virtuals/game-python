# dappier_plugin.py
import re
from typing import Dict, List, Optional, Tuple
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from dappier import Dappier

class DappierPlugin:
    def __init__(self, api_key: Optional[str] = None):
        self.dappier_client = Dappier(api_key="ak_01jkfh8zfee48swtajg7admbmk")
        
        self._functions: Dict[str, Function] = {
            "search_real_time_data": Function(
                fn_name="search_real_time_data",
                fn_description="Perform real-time data search using Dappier.",
                args=[
                    Argument(
                        name="query",
                        description="The search query for real-time data",
                        type="string",
                    )
                ],
                hint="This function is used to search for real-time data. Include ai_model_id in the query string.",
                executable=self.search_real_time_data,
            )
        }

    @property
    def available_functions(self) -> List[str]:
        return list(self._functions.keys())

    def get_function(self, fn_name: str) -> Function:
        if fn_name not in self._functions:
            raise ValueError(
                f"Function '{fn_name}' not found. Available functions: {', '.join(self.available_functions)}"
            )
        return self._functions[fn_name]

    def _serialize_response(self, response):
        """Convert RealTimeDataResponse to a dictionary"""
        if hasattr(response, '__dict__'):
            return {
                'message': response.message if hasattr(response, 'message') else str(response)
            }
        return {'message': str(response)}

    def search_real_time_data(self, query: str, **kwargs) -> Tuple[FunctionResultStatus, str, dict]:
        try:
            # Extract AI model ID from query
            ai_model_match = re.search(r'ai_model_id=([^\s]+)', query)
            if not ai_model_match:
                raise ValueError("AI model ID not found in query")
            
            ai_model_id = ai_model_match.group(1)
            # Clean the query by removing the ai_model_id part
            clean_query = re.sub(r'using ai_model_id=[^\s]+', '', query).strip()
            
            response = self.dappier_client.search_real_time_data(
                query=clean_query,
                ai_model_id=ai_model_id
            )
            
            # Serialize the response
            serialized_response = self._serialize_response(response)
            
            return (
                FunctionResultStatus.DONE,
                f"Successfully retrieved real-time data for query: {clean_query}",
                {
                    "query": clean_query,
                    "ai_model_id": ai_model_id,
                    "results": serialized_response
                },
            )
        except Exception as e:
            return (
                FunctionResultStatus.FAILED,
                f"An error occurred while fetching real-time data: {str(e)}",
                {
                    "query": query,
                },
            )