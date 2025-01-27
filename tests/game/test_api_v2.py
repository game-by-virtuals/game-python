"""Tests for the GAME API V2 client."""

import unittest
from unittest.mock import patch, MagicMock
from game_sdk.game.api_v2 import GAMEClientV2
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import Function


class TestGAMEClientV2(unittest.TestCase):
    """Test cases for the GAMEClientV2 class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = GAMEClientV2(api_key=self.api_key)

    def test_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.base_url, "https://sdk.game.virtuals.io")
        self.assertEqual(self.client.headers, {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        })

    @patch('game_sdk.game.api_v2.requests.post')
    def test_create_agent_success(self, mock_post):
        """Test successful agent creation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"id": "test_agent_id"}
        }
        mock_post.return_value = mock_response

        agent_id = self.client.create_agent(
            name="Test Agent",
            description="Test Description",
            goal="Test Goal"
        )

        self.assertEqual(agent_id, "test_agent_id")
        mock_post.assert_called_once_with(
            f"{self.client.base_url}/agents",
            headers=self.client.headers,
            json={
                "data": {
                    "name": "Test Agent",
                    "goal": "Test Goal",
                    "description": "Test Description"
                }
            }
        )

    @patch('game_sdk.game.api_v2.requests.post')
    def test_create_agent_failure(self, mock_post):
        """Test failed agent creation."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid data"}
        mock_post.return_value = mock_response

        with self.assertRaises(ValueError):
            self.client.create_agent(
                name="Test Agent",
                description="Test Description",
                goal="Test Goal"
            )

    @patch('game_sdk.game.api_v2.requests.post')
    def test_create_workers_success(self, mock_post):
        """Test successful workers creation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"id": "test_map_id"}
        }
        mock_post.return_value = mock_response

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
        self.assertEqual(call_args["headers"], self.client.headers)
        self.assertEqual(len(call_args["json"]["data"]["locations"]), 1)
        self.assertEqual(
            call_args["json"]["data"]["locations"][0]["name"],
            workers[0].id
        )

    @patch('game_sdk.game.api_v2.requests.post')
    def test_create_workers_failure(self, mock_post):
        """Test failed workers creation."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid data"}
        mock_post.return_value = mock_response

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

        with self.assertRaises(ValueError):
            self.client.create_workers(workers)

    @patch('game_sdk.game.api_v2.requests.post')
    def test_set_worker_task_success(self, mock_post):
        """Test successful worker task setting."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"task": "test_task"}
        }
        mock_post.return_value = mock_response

        result = self.client.set_worker_task(
            agent_id="test_agent",
            task="test_task"
        )

        self.assertEqual(result, {"task": "test_task"})
        mock_post.assert_called_once_with(
            f"{self.client.base_url}/agents/test_agent/tasks",
            headers=self.client.headers,
            json={
                "data": {
                    "task": "test_task"
                }
            }
        )

    @patch('game_sdk.game.api_v2.requests.post')
    def test_set_worker_task_failure(self, mock_post):
        """Test failed worker task setting."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid data"}
        mock_post.return_value = mock_response

        with self.assertRaises(ValueError):
            self.client.set_worker_task(
                agent_id="test_agent",
                task="test_task"
            )

    @patch('game_sdk.game.api_v2.requests.post')
    def test_get_worker_action_success(self, mock_post):
        """Test successful worker action retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"action": "test_action"}
        }
        mock_post.return_value = mock_response

        result = self.client.get_worker_action(
            agent_id="test_agent",
            submission_id="test_submission",
            data={"state": "test_state"}
        )

        self.assertEqual(result, {"action": "test_action"})
        mock_post.assert_called_once_with(
            f"{self.client.base_url}/agents/test_agent/tasks/test_submission/next",
            headers=self.client.headers,
            json={"state": "test_state"}
        )

    @patch('game_sdk.game.api_v2.requests.post')
    def test_get_worker_action_failure(self, mock_post):
        """Test failed worker action retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid data"}
        mock_post.return_value = mock_response

        with self.assertRaises(ValueError):
            self.client.get_worker_action(
                agent_id="test_agent",
                submission_id="test_submission",
                data={"state": "test_state"}
            )

    @patch('game_sdk.game.api_v2.requests.post')
    def test_get_agent_action_success(self, mock_post):
        """Test successful agent action retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"action": "test_action"}
        }
        mock_post.return_value = mock_response

        result = self.client.get_agent_action(
            agent_id="test_agent",
            data={"state": "test_state"}
        )

        self.assertEqual(result, {"action": "test_action"})
        mock_post.assert_called_once_with(
            f"{self.client.base_url}/agents/test_agent/actions",
            headers=self.client.headers,
            json={"state": "test_state"}
        )

    @patch('game_sdk.game.api_v2.requests.post')
    def test_get_agent_action_failure(self, mock_post):
        """Test failed agent action retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid data"}
        mock_post.return_value = mock_response

        with self.assertRaises(ValueError):
            self.client.get_agent_action(
                agent_id="test_agent",
                data={"state": "test_state"}
            )


if __name__ == '__main__':
    unittest.main()
