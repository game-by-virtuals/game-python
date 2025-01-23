"""
GameSDK module provides the main interface for interacting with the GAME API.

This module contains the GameSDK class which handles all communication with the GAME API,
including function management, simulation, and deployment of agents.
"""
from typing import Dict, List, Any, Optional

import requests
from game_sdk.game.custom_types import Function

class GameSDK:
    """
    Main interface for interacting with the GAME API.
    
    This class provides methods to manage functions, simulate agent behavior,
    and deploy agents in the GAME environment.
    
    Attributes:
        api_url (str): Base URL for the GAME API
        api_key (str): Authentication key for API access
    """
    
    api_url: str = "https://game-api.virtuals.io/api"
    api_key: str

    def __init__(self, api_key: str) -> None:
        """
        Initialize the GameSDK with an API key.
        
        Args:
            api_key (str): Authentication key for API access
            
        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        self.api_key = api_key

    def functions(self) -> Dict[str, str]:
        """
        Get all default functions available in the GAME environment.
        
        Returns:
            Dict[str, str]: Dictionary mapping function names to their descriptions
            
        Raises:
            Exception: If the API request fails
        """
        response = requests.get(
            f"{self.api_url}/functions",
            headers={"x-api-key": self.api_key}
        )

        if response.status_code != 200:
            raise Exception(response.json())

        functions: Dict[str, str] = {}
        for x in response.json()["data"]:
            functions[x["fn_name"]] = x["fn_description"]

        return functions

    def simulate(
        self,
        session_id: str,
        goal: str,
        description: str,
        world_info: str,
        functions: List[Any],
        custom_functions: List[Function]
    ) -> Dict[str, Any]:
        """
        Simulate agent behavior with the given configuration.
        
        Args:
            session_id (str): Unique identifier for the simulation session
            goal (str): The goal or objective for the agent
            description (str): Description of the agent's role or context
            world_info (str): Information about the environment
            functions (List[Any]): List of available functions
            custom_functions (List[Function]): List of custom functions
            
        Returns:
            Dict[str, Any]: Simulation results from the API
            
        Raises:
            Exception: If the API request fails
        """
        payload = {
            "sessionId": session_id,
            "goal": goal,
            "description": description,
            "worldInfo": world_info,
            "functions": functions,
            "customFunctions": ([x.toJson() for x in custom_functions] 
                              if custom_functions and hasattr(custom_functions[0], 'toJson') 
                              else custom_functions)
        }

        response = requests.post(
            f"{self.api_url}/simulate",
            json={"data": payload},
            headers={"x-api-key": self.api_key}
        )

        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()["data"]

    def react(
        self,
        session_id: str,
        platform: str,
        goal: str,
        description: str,
        world_info: str,
        functions: List[Any],
        custom_functions: List[Function],
        event: Optional[str] = None,
        task: Optional[str] = None,
        tweet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate the agent configuration.
        
        Args:
            session_id (str): Unique identifier for the simulation session
            platform (str): Platform for the simulation
            goal (str): The goal or objective for the agent
            description (str): Description of the agent's role or context
            world_info (str): Information about the environment
            functions (List[Any]): List of available functions
            custom_functions (List[Function]): List of custom functions
            event (Optional[str]): Event for the simulation
            task (Optional[str]): Task for the simulation
            tweet_id (Optional[str]): Tweet ID for the simulation
            
        Returns:
            Dict[str, Any]: Simulation results from the API
            
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.api_url}/react/{platform}"

        payload = {
            "sessionId": session_id,
            "goal": goal,
            "description": description,
            "worldInfo": world_info,
            "functions": functions,
            "customFunctions": [x.toJson() for x in custom_functions]
        }

        if event:
            payload["event"] = event

        if task:
            payload["task"] = task
            
        if tweet_id:
            payload["tweetId"] = tweet_id
            
        print(payload)

        response = requests.post(
            url,
            json={
                "data": payload
            },
            headers={"x-api-key": self.api_key}
        )

        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()["data"]

    def deploy(
        self,
        goal: str,
        description: str,
        world_info: str,
        functions: List[Any],
        custom_functions: List[Function],
        main_heartbeat: int,
        reaction_heartbeat: int
    ) -> Dict[str, Any]:
        """
        Simulate the agent configuration.
        
        Args:
            goal (str): The goal or objective for the agent
            description (str): Description of the agent's role or context
            world_info (str): Information about the environment
            functions (List[Any]): List of available functions
            custom_functions (List[Function]): List of custom functions
            main_heartbeat (int): Main heartbeat for the simulation
            reaction_heartbeat (int): Reaction heartbeat for the simulation
            
        Returns:
            Dict[str, Any]: Simulation results from the API
            
        Raises:
            Exception: If the API request fails
        """
        response = requests.post(
            f"{self.api_url}/deploy",
            json={
                "data": {
                    "goal": goal,
                    "description": description,
                    "worldInfo": world_info,
                    "functions": functions,
                    "customFunctions": [x.toJson() for x in custom_functions],
                    "gameState" : {
                        "mainHeartbeat" : main_heartbeat,
                        "reactionHeartbeat" : reaction_heartbeat,
                    }
                }
            },
            headers={"x-api-key": self.api_key}
        )

        if response.status_code != 200:
            raise Exception(response.json())

        return response.json()["data"]
