import requests
from typing import List, Dict, Optional


class GAMEClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://game.virtuals.io"
        
    def _get_access_token(self) -> str:
        """
        Internal method to get access token
        """
        response = requests.post(
            "https://api.virtuals.io/api/accesses/tokens",
            json={"data": {}},
            headers={"x-api-key": self.api_key},
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to get token (status {response.status_code}). Response: {response.text}")

        response_json = response.json()
        return response_json["data"]["accessToken"]

    def _post(
        self, endpoint: str, data: dict, extra_headers: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Internal method to post data
        """
        access_token = self._get_access_token()

        # Default headers with Authorization
        headers = {"Authorization": f"Bearer {access_token}"}

        # Merge additional headers if provided
        if extra_headers:
            headers.update(extra_headers)

        response = requests.post(
            f"{self.base_url}/prompts",
            json={
                "data": {
                    "method": "post",
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "route": endpoint,
                    "data": data,
                },
            },
            headers=headers,
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to post data (status {response.status_code}). Response: {response.text}")

        response_json = response.json()
        return response_json["data"]

    def create_agent(self, name: str, description: str, goal: str) -> str:
        """
        Create an agent instance (worker or agent with task generator)
        """
        create_agent_response = self._post(
            endpoint="/v2/agents",
            data={
                "name": name,
                "description": description,
                "goal": goal,
            }
        )

        return create_agent_response["id"]

    def create_workers(self, workers: List) -> str:
        """
        Create workers and worker description for the task generator (for agent)
        """
        res = self._post(
            endpoint="/v2/maps",
            data={
                "locations": [
                    {"id": w.id, "name": w.id, "description": w.worker_description}
                    for w in workers
                ]
            },
        )

        return res["id"]

    def set_worker_task(self, agent_id: str, task: str) -> Dict:
        """
        Set worker task (for standalone worker)
        """
        return self._post(
            endpoint=f"/v2/agents/{agent_id}/tasks",
            data={"task": task},
        )

    def get_worker_action(
        self,
        agent_id: str,
        submission_id: str,
        data: dict,
        model_name: str,
    ) -> Dict:
        """
        Get worker actions (for standalone worker)
        """
        return self._post(
            endpoint=f"/v2/agents/{agent_id}/tasks/{submission_id}/next",
            data=data,
            extra_headers={"model_name": model_name},
        )

    def get_agent_action(self, agent_id: str, data: dict, model_name: str) -> Dict:
        """
        Get agent actions/next step (for agent)
        """
        return self._post(
            endpoint=f"/v2/agents/{agent_id}/actions",
            data=data,
            extra_headers={"model_name": model_name},
        )