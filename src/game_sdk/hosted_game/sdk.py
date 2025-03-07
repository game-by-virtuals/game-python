import requests
import json


class GameSDK:
    api_url: str = "https://game-api.virtuals.io/api"
    api_key: str

    def __init__(self, api_key: str):
        self.api_key = api_key

    def functions(self):
        """
        Get all default functions
        """
        response = requests.get(
            f"{self.api_url}/functions", headers={"x-api-key": self.api_key})

        if (response.status_code != 200):
            raise Exception(response.json())

        functions = {}

        for x in response.json()["data"]:
            functions[x["fn_name"]] = x["fn_description"]

        return functions

    def simulate(self, session_id: str,  goal: str, description: str, world_info: str, functions: list, custom_functions: list):
        """
        Simulate the agent configuration
        """
        response = requests.post(
            f"{self.api_url}/simulate",
            json={
                "data": {
                    "sessionId": session_id,
                    "goal": goal,
                    "description": description,
                    "worldInfo": world_info,
                    "functions": functions,
                    "customFunctions": [x.toJson() for x in custom_functions]
                }
            },
            headers={"x-api-key": self.api_key}
        )

        if (response.status_code != 200):
            raise Exception(response.json())

        return response.json()["data"]

    def react(self, session_id: str, platform: str, goal: str,
              description: str, world_info: str, functions: list, custom_functions: list,
              event: str = None, task: str = None, tweet_id: str = None):
        """
        Simulate the agent configuration
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

        if (event):
            payload["event"] = event

        if (task):
            payload["task"] = task
            
        if (tweet_id):
            payload["tweetId"] = tweet_id
            
        print(payload)

        response = requests.post(
            url,
            json={
                "data": payload
            },
            headers={"x-api-key": self.api_key}
        )

        if (response.status_code != 200):
            raise Exception(response.json())

        return response.json()["data"]

    def deploy(self, goal: str, description: str, world_info: str, functions: list, custom_functions: list, main_heartbeat: int, reaction_heartbeat: int, tweet_usernames: list = None, templates: list = None, game_engine_model: str = "llama_3_1_405b"):
        """
        Simulate the agent configuration
        """
        payload = {
            "goal": goal,
            "description": description,
            "worldInfo": world_info,
            "functions": functions,
            "customFunctions": [x.toJson() for x in custom_functions],
            "gameState": {
                "mainHeartbeat": main_heartbeat,
                "reactionHeartbeat": reaction_heartbeat,
            },
            "gameEngineModel": game_engine_model
        }
            
        if tweet_usernames is not None:
            payload["tweetUsernames"] = tweet_usernames
            
        # Add templates to payload if provided
        if templates:
            payload["templates"] = [template.to_dict() for template in templates]   
            
        response = requests.post(
            f"{self.api_url}/deploy",
            json={
                "data": payload
            },
            headers={"x-api-key": self.api_key}
        )

        if (response.status_code != 200):
            raise Exception(response.json())

        return response.json()["data"]
    
    def reset_memory(self):
        response = requests.get(
            f"{self.api_url}/reset-session", headers={"x-api-key": self.api_key})

        if (response.status_code != 200):
            raise Exception("Failed to reset memory.")

        return "Memory reset successfully."

    def export_to_sandbox(self, goal: str, description: str, world_info: str, enabled_functions: list, 
              custom_functions: list, main_heartbeat: int, reaction_heartbeat: int, task_description: str,
              templates: list, game_engine_model: str = "llama_3_1_405b") -> dict:
        """Export all initialization fields of the Agent as a dictionary"""

        templates_dicts = [template.to_dict() for template in templates]

        shared_template = {
            "startTemplate": "",
            "template": "",
            "endTemplate": ""
        }

        post_template = None
        reply_template = None

        # Process templates
        if templates_dicts:
            for template_dict in templates_dicts:
                # Handle shared templates
                if template_dict["templateType"] == "TWITTER_START_SYSTEM_PROMPT":
                    shared_template["startTemplate"] = template_dict["systemPrompt"]
                elif template_dict["templateType"] == "SHARED":
                    shared_template["template"] = template_dict["systemPrompt"]
                elif template_dict["templateType"] == "TWITTER_END_SYSTEM_PROMPT":
                    shared_template["endTemplate"] = template_dict["systemPrompt"]
                # Handle POST and REPLY templates
                elif template_dict["type"] == "POST":
                    post_template = template_dict
                elif template_dict["type"] == "REPLY":
                    reply_template = template_dict

        export_dict = {
            "goal": goal,
            "description": description,
            "worldInfo": world_info,
            "mainHeartbeat": main_heartbeat,
            "reactionHeartbeat": reaction_heartbeat,
            "taskDescription": task_description,
            "gameEngineModel": game_engine_model,
            "functions": enabled_functions,
            "customFunctions": [x.toJson() for x in custom_functions],
            "sharedTemplate": shared_template
        }

        # Add POST and REPLY templates if they exist
        if post_template:
            post_template["isSandbox"] = True  # Force isSandbox to True
            export_dict["postTemplate"] = post_template
        if reply_template:
            reply_template["isSandbox"] = True  # Force isSandbox to True
            export_dict["replyTemplate"] = reply_template

        print("Exported Agent Configuration:")
        print(json.dumps(export_dict, indent=4))

        return export_dict

