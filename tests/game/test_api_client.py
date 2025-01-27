"""Tests for the GAME API client."""

import unittest
from unittest.mock import patch, MagicMock
import requests
import tenacity
from game_sdk.game.api_client import GameAPIClient, should_retry
from game_sdk.game.exceptions import APIError, AuthenticationError, ValidationError


class TestGameAPIClient(unittest.TestCase):
    """Test cases for the GameAPIClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = GameAPIClient(api_key=self.api_key)

    def test_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertIsInstance(self.client.session, requests.Session)
        self.assertEqual(
            self.client.session.headers["Authorization"],
            f"Bearer {self.api_key}"
        )
        self.assertEqual(
            self.client.session.headers["Content-Type"],
            "application/json"
        )

    def test_initialization_no_api_key(self):
        """Test initialization without API key."""
        with self.assertRaises(ValueError):
            GameAPIClient(api_key=None)

    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        result = self.client.make_request(
            method="GET",
            endpoint="/test",
            data={"key": "value"},
            params={"param": "value"}
        )

        self.assertEqual(result, {"data": "test"})
        mock_request.assert_called_once_with(
            method="GET",
            url=f"{self.client.base_url}/test",
            json={"key": "value"},
            params={"param": "value"}
        )

    @patch('requests.Session.request')
    def test_make_request_auth_error(self, mock_request):
        """Test authentication error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            self.client.make_request("GET", "/test")

    @patch('requests.Session.request')
    def test_make_request_validation_error(self, mock_request):
        """Test validation error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.client.make_request("GET", "/test")

    @patch('requests.Session.request')
    def test_make_request_api_error(self, mock_request):
        """Test API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with self.assertRaises(APIError):
            try:
                self.client.make_request("GET", "/test")
            except tenacity.RetryError as e:
                raise e.last_attempt.result()

    @patch('requests.Session.request')
    def test_make_request_network_error(self, mock_request):
        """Test network error handling."""
        mock_request.side_effect = requests.exceptions.ConnectionError()

        with self.assertRaises(APIError):
            try:
                self.client.make_request("GET", "/test")
            except tenacity.RetryError as e:
                raise e.last_attempt.result()

    @patch('game_sdk.game.api_client.GameAPIClient.make_request')
    def test_get_request(self, mock_make_request):
        """Test GET request."""
        mock_make_request.return_value = {"data": "test"}
        result = self.client.get("/test", params={"param": "value"})

        self.assertEqual(result, {"data": "test"})
        mock_make_request.assert_called_once_with(
            "GET",
            "/test",
            params={"param": "value"}
        )

    @patch('game_sdk.game.api_client.GameAPIClient.make_request')
    def test_post_request(self, mock_make_request):
        """Test POST request."""
        mock_make_request.return_value = {"data": "test"}
        result = self.client.post("/test", data={"key": "value"})

        self.assertEqual(result, {"data": "test"})
        mock_make_request.assert_called_once_with(
            "POST",
            "/test",
            data={"key": "value"}
        )

    @patch('game_sdk.game.api_client.GameAPIClient.make_request')
    def test_put_request(self, mock_make_request):
        """Test PUT request."""
        mock_make_request.return_value = {"data": "test"}
        result = self.client.put("/test", data={"key": "value"})

        self.assertEqual(result, {"data": "test"})
        mock_make_request.assert_called_once_with(
            "PUT",
            "/test",
            data={"key": "value"}
        )

    @patch('game_sdk.game.api_client.GameAPIClient.make_request')
    def test_delete_request(self, mock_make_request):
        """Test DELETE request."""
        mock_make_request.return_value = {"data": "test"}
        result = self.client.delete("/test")

        self.assertEqual(result, {"data": "test"})
        mock_make_request.assert_called_once_with(
            "DELETE",
            "/test"
        )

    def test_should_retry(self):
        """Test retry condition function."""
        # Should retry on APIError
        self.assertTrue(should_retry(APIError("test")))
        
        # Should retry on RequestException
        self.assertTrue(should_retry(requests.exceptions.RequestException()))
        
        # Should not retry on AuthenticationError
        self.assertFalse(should_retry(AuthenticationError("test")))
        
        # Should not retry on ValidationError
        self.assertFalse(should_retry(ValidationError("test")))


if __name__ == '__main__':
    unittest.main()
