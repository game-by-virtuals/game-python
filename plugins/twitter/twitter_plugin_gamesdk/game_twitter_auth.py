import argparse
import threading

import requests
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from typing import Optional
from dataclasses import dataclass

BASE_URL = "https://twitter.game.virtuals.io/accounts"


@dataclass
class AuthCredentials:
    """
    Data class to hold authentication credentials.
    """
    api_key: str
    access_token: Optional[str] = None


class AuthHandler(BaseHTTPRequestHandler):
    """
    Handles OAuth authentication callback from Twitter.
    """

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/callback":
            query_params = parse_qs(parsed_url.query)
            code: Optional[str] = query_params.get("code", [None])[0]
            state: Optional[str] = query_params.get("state", [None])[0]

            if code and state:
                access_token = AuthManager.verify_auth(code, state)
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Authentication successful! You may close this window and return to the terminal.")
                print("Authenticated! Here's your access token:")
                print(access_token)
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid request")
                print("Authentication failed! Please try again.")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            print("Not Found")

        threading.Thread(target=self.server.shutdown, daemon=True).start() # Stop the server after handling the request

    def log_message(self, format, *args):
        pass


class AuthManager:
    """
    Manages OAuth authentication flow.
    """

    @staticmethod
    def get_login_url(api_key: str) -> str:
        """
        Fetches the login URL from the authentication server.
        """
        response = requests.get(f"{BASE_URL}/auth", headers={"x-api-key": api_key})
        response.raise_for_status()
        return response.json().get("url")

    @staticmethod
    def verify_auth(code: str, state: str) -> str:
        """
        Verifies authentication and retrieves an access token.
        """
        response = requests.get(f"{BASE_URL}/verify", params={"code": code, "state": state})
        response.raise_for_status()
        return response.json().get("token")

    @staticmethod
    def start_authentication(api_key: str, port: int = 8714) -> None:
        """
        Starts a temporary web server to handle authentication.
        """
        SERVER_ADDRESS = ("", port)
        HANDLER_CLASS = AuthHandler
        with HTTPServer(SERVER_ADDRESS, HANDLER_CLASS) as server:
            login_url = AuthManager.get_login_url(api_key)
            print("\nWaiting for authentication...\n")
            print("Visit the following URL to authenticate:")
            print(login_url + "\n")
            webbrowser.open(login_url)
            server.serve_forever()

def start() -> None:
    """
    Entry point for the game twitter auth process.
    """
    parser = argparse.ArgumentParser(prog="game-twitter-plugin", description="CLI to authenticate and interact with GAME's Twitter API")
    parser.add_argument("auth", help="Authenticate with Twitter API", nargs='?')
    parser.add_argument("-k", "--key", help="Project's API key", required=True, type=str)
    args = parser.parse_args()
    AuthManager.start_authentication(args.key)

if __name__ == "__main__":
    start()