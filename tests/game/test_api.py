"""Tests for the GAME API client."""

import unittest
from unittest.mock import patch, MagicMock
from game_sdk.game.api import GAMEClient
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import Function


class TestGAMEClient(unittest.TestCase):
    """Test cases for the GAMEClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = GAMEClient(self.api_key)

    def test_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.base_url, "https://game.virtuals.io")

    @patch('game_sdk.game.api.requests.post')
    def test_get_access_token_success(self, mock_post):
        """Test successful access token retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"accessToken": "test_token"}
        }
        mock_post.return_value = mock_response

        token = self.client._get_access_token()
        self.assertEqual(token, "test_token")

        mock_post.assert_called_once_with(
            "https://api.virtuals.io/api/accesses/tokens",
            json={"data": {}},
            headers={"x-api-key": self.api_key}
        )

    @patch('game_sdk.game.api.requests.post')
    def test_get_access_token_failure(self, mock_post):
        """Test failed access token retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_post.return_value = mock_response

        with self.assertRaises(ValueError):
            self.client._get_access_token()

    @patch('game_sdk.game.api.GAMEClient._get_access_token')
    @patch('game_sdk.game.api.requests.post')
    def test_post_success(self, mock_post, mock_get_token):
        """Test successful post request."""
        mock_get_token.return_value = "test_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"result": "success"}
        }
        mock_post.return_value = mock_response

        result = self.client._post("/test", {"key": "value"})
        self.assertEqual(result, {"result": "success"})

        mock_post.assert_called_once_with(
            f"{self.client.base_url}/prompts",
            json={
                "data": {
                    "method": "post",
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "route": "/test",
                    "data": {"key": "value"},
                },
            },
            headers={"Authorization": "Bearer test_token"},
        )

    @patch('game_sdk.game.api.GAMEClient._post')
    def test_create_agent(self, mock_post):
        """Test agent creation."""
        mock_post.return_value = {"id": "test_agent_id"}

        agent_id = self.client.create_agent(
            name="Test Agent",
            description="Test Description",
            goal="Test Goal"
        )

        self.assertEqual(agent_id, "test_agent_id")
        mock_post.assert_called_once_with(
            endpoint="/v2/agents",
            data={
                "name": "Test Agent",
                "description": "Test Description",
                "goal": "Test Goal",
            }
        )

    @patch('game_sdk.game.api.GAMEClient._post')
    def test_create_workers(self, mock_post):
        """Test workers creation."""
        mock_post.return_value = {"id": "test_map_id"}

        workers = [
            WorkerConfig(
                worker_name="Test Worker",
                worker_description="Test Description",
                functions=[
                    Function(
                        fn_name="test_fn",
                        fn_description="Test Function",
                        args=[]
                    )
                ]
            )
        ]

        map_id = self.client.create_workers(workers)
        self.assertEqual(map_id, "test_map_id")

        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        self.assertEqual(call_args["endpoint"], "/v2/maps")
        self.assertEqual(len(call_args["data"]["locations"]), 1)
        self.assertEqual(call_args["data"]["locations"][0]["name"], workers[0].id)

    @patch('game_sdk.game.api.GAMEClient._post')
    def test_set_worker_task(self, mock_post):
        """Test setting worker task."""
        mock_post.return_value = {"task": "test_task"}

        result = self.client.set_worker_task(
            agent_id="test_agent",
            task="test_task"
        )

        self.assertEqual(result, {"task": "test_task"})
        mock_post.assert_called_once_with(
            endpoint="/v2/agents/test_agent/tasks",
            data={"task": "test_task"}
        )

    @patch('game_sdk.game.api.GAMEClient._post')
    def test_get_worker_action(self, mock_post):
        """Test getting worker action."""
        mock_post.return_value = {"action": "test_action"}

        result = self.client.get_worker_action(
            agent_id="test_agent",
            submission_id="test_submission",
            data={"state": "test_state"}
        )

        self.assertEqual(result, {"action": "test_action"})
        mock_post.assert_called_once_with(
            endpoint="/v2/agents/test_agent/tasks/test_submission/next",
            data={"state": "test_state"}
        )

    @patch('game_sdk.game.api.GAMEClient._post')
    def test_get_agent_action(self, mock_post):
        """Test getting agent action."""
        mock_post.return_value = {"action": "test_action"}

        result = self.client.get_agent_action(
            agent_id="test_agent",
            data={"state": "test_state"}
        )

        self.assertEqual(result, {"action": "test_action"})
        mock_post.assert_called_once_with(
            endpoint="/v2/agents/test_agent/actions",
            data={"state": "test_state"}
        )


if __name__ == '__main__':
    unittest.main()
