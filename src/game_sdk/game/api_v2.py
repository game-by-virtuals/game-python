import requests
from typing import List, Dict

class GAMEClientV2:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://sdk.game.virtuals.io/v2"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }

    def create_agent(self, name: str, description: str, goal: str) -> str:
        """
        API call to create an agent instance (worker or agent with task generator)
        """
        payload = {
            "data": {
                "name": name,
                "goal": goal,
                "description": description
            }
        }

        response = requests.post(
            f"{self.base_url}/agents",
            headers=self.headers,
            json=payload
        )

        return self._get_response_body(response)["id"]

    def create_workers(self, workers: List) -> str:
        """
        API call to create workers and worker description for the task generator (agent)
        """
        payload = {
            "data": {
                "locations": [
                    {"id": w.id, "name": w.id, "description": w.worker_description}
                    for w in workers
                ]
            }
        }

        response = requests.post(
            f"{self.base_url}/maps",
            headers=self.headers,
            json=payload
        )

        return self._get_response_body(response)["id"]

    def set_worker_task(self, agent_id: str, task: str) -> Dict:
        """
        API call to set worker task (for standalone worker)
        """
        payload = {
            "data": {
                "task": task
            }
        }

        response = requests.post(
            f"{self.base_url}/agents/{agent_id}/tasks",
            headers=self.headers,
            json=payload
        )

        return self._get_response_body(response)

    def get_worker_action(self, agent_id: str, submission_id: str, data: dict, model_name: str) -> Dict:
        """
        API call to get worker actions (for standalone worker)
        """
        response = requests.post(
            f"{self.base_url}/agents/{agent_id}/tasks/{submission_id}/next",
            headers=self.headers | {"model_name": model_name},
            json={
                "data": data
            }
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get worker action (status {response.status_code}). Response: {response.text}")

        response_json = response.json()

        return response_json["data"]

    def get_agent_action(self, agent_id: str, data: dict, model_name: str) -> Dict:
        """
        API call to get agent actions/next step (for agent)
        """
        response = requests.post(
            f"{self.base_url}/agents/{agent_id}/actions",
            headers=self.headers | {"model_name": model_name},
            json={
                "data": data
            }
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get agent action (status {response.status_code}). Response: {response.text}")

        response_json = response.json()

        return response_json["data"]
    
    def create_chat(self, data: dict) -> str:
        response = requests.post(
            f"{self.base_url}/conversation",
            headers=self.headers,
            json={
                "data": data
            }
        )
        
        chat_id = self._get_response_body(response).get("conversation_id")
        if not chat_id:
            raise Exception("Agent did not return a conversation_id for the chat.")
        return chat_id
    
    def update_chat(self, conversation_id: str, data: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/conversation/{conversation_id}/next",
            headers=self.headers,
            json={
                "data": data
            }
        )
        
        if response.status_code != 200:
            raise ValueError(f"Failed to update conversation (status {response.status_code}). Response: {response.text}")

        response_json = response.json()

        return response_json["data"]
    
    def report_function(self, conversation_id: str, data: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/conversation/{conversation_id}/function/result",
            headers=self.headers,
            json={
                "data": data
            }
        )

        return self._get_response_body(response)
    
    def end_chat(self, conversation_id: str, data: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/conversation/{conversation_id}/end",
            headers=self.headers,
            json={
                "data": data
            }
        )

        return self._get_response_body(response)
    
    def _get_response_body(self, response: requests.Response) -> dict:
        if response.status_code != 200:
            raise ValueError(f"Failed to get response body (status {response.status_code}). Response: {response.text}")

        response_json = response.json()

        return response_json["data"]