import json
import requests_unixsocket
from requests import HTTPError
import hashlib
import jwt
import logging
from typing import Dict, Callable, Any, Optional, List, Callable

Audience = "http://aizel.com"

class CustomToken:
    def __init__(self, audience, nonce, token_type="OIDC"):
        self.audience = audience
        self.nonces = [nonce]
        self.token_type = token_type

class GcpConfidentialSpace:
    def __init__(self, audience: str):
        self.audience = audience

    def attestation_report(self, nonce: str) -> str:
        try:
            hashed_nonce = hashlib.sha256(nonce.encode('utf-8')).hexdigest()
            request = CustomToken(self.audience, hashed_nonce)
            session = requests_unixsocket.Session()
            url = 'http+unix://%2Frun%2Fcontainer_launcher%2Fteeserver.sock/v1/token'
            headers = {'Content-Type': 'application/json'}
            custom_json = json.dumps(request.__dict__)
            response = session.post(url, headers=headers, data=custom_json)
            response.raise_for_status()
            return response.content.decode('utf-8')
        except Exception as err:
            raise RuntimeError(f"{err}")


class TeePlugin:
    def __init__(self, options: Dict[str, Any]) -> None:
        self.id: str = options.get("id", "tee_plugin")
        self.name: str = options.get("name", "TEE Plugin")
        self.description: str = options.get(
            "description",
            "A plugin that obtains the attestation report in the Trusted Execution Environment.",
        )
        # tee plugin type, current only support Google Confidential Space
        self.type: str = options.get("tee_type", "GCS")

        # Define internal function mappings
        self._functions: Dict[str, Callable[..., Any]] = {
            "get_attestation_report": self._get_attestation_report,
        }

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger: logging.Logger = logging.getLogger(__name__)

    def get_function(self, fn_name: str) -> Callable:
        """
        Get a specific function by name.

        Args:
            fn_name: Name of the function to retrieve

        Raises:
            ValueError: If function name is not found

        Returns:
            Function object
        """
        if fn_name not in self._functions:
            raise ValueError(
                f"Function '{fn_name}' not found. Available functions: {', '.join(self.available_functions)}"
            )
        return self._functions[fn_name]

    def _get_attestation_report(self, nonce: str) -> str:
        if self.type == "GCS":
            try:
                gcp = GcpConfidentialSpace(Audience)
                gcp.attestation_report(nonce)
            except RuntimeError as e:
                self.logger.error(f"Failed to get attestation report for Google confidential space: {e}")
                return ""
        else: 
            raise ValueError(
                f"Unsupport tee backend type '{self.type}'. Available type: GCS"
            )

def decode_gcp_attestation_report(report: str) -> dict:
    try:
        decoded_report = jwt.decode(report, options={"verify_signature": False})
        return decoded_report
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")