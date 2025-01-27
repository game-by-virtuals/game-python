"""Tests for the GAME SDK utilities."""

import unittest
from unittest.mock import patch, MagicMock
import requests
from game_sdk.game.utils import (
    post,
    create_agent,
    create_workers,
    validate_response,
    format_endpoint,
    merge_params,
    parse_api_error
)
from game_sdk.game.exceptions import APIError, AuthenticationError, ValidationError
from game_sdk.game.worker_config import WorkerConfig
from game_sdk.game.custom_types import Function


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://api.virtuals.io"
        self.api_key = "test_api_key"

    @patch('game_sdk.game.utils.requests.post')
    def test_post_success(self, mock_post):
        """Test successful POST request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"result": "success"}}
        mock_post.return_value = mock_response

        result = post(
            base_url=self.base_url,
            api_key=self.api_key,
            endpoint="/test",
            data={"key": "value"}
        )

        self.assertEqual(result, {"result": "success"})
        mock_post.assert_called_once_with(
            f"{self.base_url}/test",
            json={"key": "value"},
            params=None,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30
        )

    @patch('game_sdk.game.utils.requests.post')
    def test_post_auth_error(self, mock_post):
        """Test authentication error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            post(
                base_url=self.base_url,
                api_key=self.api_key,
                endpoint="/test"
            )

    @patch('game_sdk.game.utils.requests.post')
    def test_post_validation_error(self, mock_post):
        """Test validation error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"message": "Invalid data"}
        }
        mock_post.return_value = mock_response

        with self.assertRaises(ValidationError):
            post(
                base_url=self.base_url,
                api_key=self.api_key,
                endpoint="/test"
            )

    @patch('game_sdk.game.utils.requests.post')
    def test_post_rate_limit_error(self, mock_post):
        """Test rate limit error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        with self.assertRaises(APIError) as context:
            post(
                base_url=self.base_url,
                api_key=self.api_key,
                endpoint="/test"
            )
        self.assertEqual(str(context.exception), "Rate limit exceeded")

    @patch('game_sdk.game.utils.requests.post')
    def test_post_server_error(self, mock_post):
        """Test server error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        with self.assertRaises(APIError) as context:
            post(
                base_url=self.base_url,
                api_key=self.api_key,
                endpoint="/test"
            )
        self.assertEqual(str(context.exception), "Server error")

    @patch('game_sdk.game.utils.requests.post')
    def test_post_connection_error(self, mock_post):
        """Test connection error handling."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with self.assertRaises(APIError) as context:
            post(
                base_url=self.base_url,
                api_key=self.api_key,
                endpoint="/test"
            )
        self.assertTrue("Connection failed" in str(context.exception))

    @patch('game_sdk.game.utils.post')
    def test_create_agent_success(self, mock_post):
        """Test successful agent creation."""
        mock_post.return_value = {"id": "test_agent_id"}

        agent_id = create_agent(
            base_url=self.base_url,
            api_key=self.api_key,
            name="Test Agent",
            description="Test Description",
            goal="Test Goal"
        )

        self.assertEqual(agent_id, "test_agent_id")
        mock_post.assert_called_once_with(
            self.base_url,
            self.api_key,
            endpoint="/v2/agents",
            data={
                "name": "Test Agent",
                "description": "Test Description",
                "goal": "Test Goal"
            }
        )

    @patch('game_sdk.game.utils.post')
    def test_create_workers_success(self, mock_post):
        """Test successful workers creation."""
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

        map_id = create_workers(
            base_url=self.base_url,
            api_key=self.api_key,
            workers=workers
        )

        self.assertEqual(map_id, "test_map_id")
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0], (self.base_url, self.api_key))
        self.assertEqual(call_args[1]["endpoint"], "/v2/maps")
        self.assertEqual(len(call_args[1]["data"]["locations"]), 1)
        self.assertEqual(
            call_args[1]["data"]["locations"][0]["name"],
            workers[0].id
        )

    def test_validate_response_success(self):
        """Test successful response validation."""
        response = {
            "status": "success",
            "data": {"result": "test"}
        }
        validate_response(response)  # Should not raise any exception

    def test_validate_response_failure(self):
        """Test failed response validation."""
        invalid_responses = [
            None,
            {},
            {"status": "error"},
            {"data": None}
        ]
        for response in invalid_responses:
            with self.assertRaises(ValueError):
                validate_response(response)

    def test_format_endpoint(self):
        """Test endpoint formatting."""
        test_cases = [
            ("test", "/test"),
            ("/test", "/test"),
            ("//test", "/test"),
            ("test/", "/test"),
            ("/test/", "/test"),
            ("", "/"),
            ("/", "/")
        ]
        for input_endpoint, expected_output in test_cases:
            self.assertEqual(format_endpoint(input_endpoint), expected_output)

    def test_merge_params(self):
        """Test parameter merging."""
        test_cases = [
            (None, None, {}),
            ({}, {}, {}),
            ({"a": 1}, None, {"a": 1}),
            (None, {"b": 2}, {"b": 2}),
            ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
            ({"a": 1}, {"a": 2}, {"a": 2})  # Additional params override base params
        ]
        for base_params, additional_params, expected_output in test_cases:
            self.assertEqual(
                merge_params(base_params, additional_params),
                expected_output
            )

    def test_parse_api_error(self):
        """Test API error parsing."""
        test_cases = [
            (
                {"error": {"message": "Test error"}},
                "Test error"
            ),
            (
                {"error": {"detail": "Test detail"}},
                "Test detail"
            ),
            (
                {"message": "Direct message"},
                "Direct message"
            ),
            (
                {},
                "Unknown error"
            )
        ]
        for error_response, expected_message in test_cases:
            self.assertEqual(parse_api_error(error_response), expected_message)


if __name__ == '__main__':
    unittest.main()
