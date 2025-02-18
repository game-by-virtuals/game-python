from typing import Dict, Any, Optional, List, Union, TypedDict, Callable, Literal

import json
import os
import time
import web3
import requests
import threading
import logging
from web3.contract import Contract
from web3.middleware.signing import SignAndSendRawMiddlewareBuilder


class MemeInfo(TypedDict):
    address: str
    name: str
    symbol: str
    description: str
    progress: str  # a float in string, 0~100

AVAILABLE_FUNCTIONS = Literal["create_meme", "get_meme_list"]

class ConfluxPlugin:
    def __init__(self, options: Dict[str, Any]) -> None:
        self.id: str = options.get("id", "conflux_plugin")
        self.name: str = options.get("name", "Conflux Plugin")
        self.description: str = options.get(
            "description",
            "A plugin that executes tasks within Conflux, especially for pumping.",
        )

        credentials: Optional[Dict[str, str]] = options.get("credentials")
        if not credentials:
            raise ValueError("Conflux API credentials are required.")

        # default to Conflux espace mainnet
        self.w3 = web3.Web3(
            web3.HTTPProvider(
                credentials.get("rpc_url") or "https://evm.confluxrpc.com"
            )
        )
        account = self.w3.eth.account.from_key(credentials.get("private_key"))
        self.w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(account), layer=0)  # type: ignore
        self.w3.eth.default_account = account.address

        confi_pump_helper_url = credentials.get("confi_pump_helper_url")
        if not confi_pump_helper_url:
            raise ValueError("Confi Pump Helper URL is required.")

        self.confi_pump_helper_url = confi_pump_helper_url

        address = credentials.get("contract_address")

        if not address:
            raise ValueError("Contract address is required.")

        meme_abi = json.load(
            open(os.path.join(os.path.dirname(__file__), "abi", "meme.json"))
        )
        self.meme_contract: Contract = self.w3.eth.contract(address=address, abi=meme_abi)  # type: ignore

    @property
    def available_functions(self) -> List[str]:
        return [
            "create_meme",
            # "sell_meme",
            # "buy_meme",
            "get_meme_list",
        ]

    def get_function(self, fn_name: AVAILABLE_FUNCTIONS) -> Callable:
        """
        Get a specific function by name.

        Args:
            fn_name: Name of the function to retrieve

        Returns:
            Function object
        """
        if fn_name == "create_meme":
            return self._create_meme
        elif fn_name == "get_meme_list":
            return self._get_meme_list
        else:
            raise ValueError(f"Function '{fn_name}' not found. Available functions: {', '.join(self.available_functions)}")

    def _get_cid(self, meme_image_url: str) -> str:
        headers = {"Content-Type": "application/json"}

        payload = {"imageUrl": meme_image_url}

        try:
            response = requests.post(
                f"{self.confi_pump_helper_url}/api/getCID",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()  # 如果状态码不是200，抛出异常

            data = response.json()
            return data.get("cid")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to get CID: {e}")

    # called after meme is created and confirmed (safe tag)
    def _upload_meme_image(self, meme_image_url: str) -> None:
        headers = {"Content-Type": "application/json"}

        payload = {"imageUrl": meme_image_url}

        response = requests.post(
            f"{self.confi_pump_helper_url}/api/uploadToIPFS",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

    # returns the token address
    def _create_meme(
        self,
        name: str,
        symbol: str,
        description: str,
        image_url: str,
    ) -> None:
        cid = self._get_cid(image_url)
        meta = {
            "description": description,
            "image": cid,
        }
        h = self.meme_contract.functions.newToken(
            name=name, symbol=symbol, meta=json.dumps(meta)
        ).transact({
            "value": self.w3.to_wei(10, "ether"),
            "gas": 1000000,
        })
        receipt = self.w3.eth.wait_for_transaction_receipt(h)
        if receipt["status"] != 1:
            raise ValueError("Failed to create meme")

        processed_logs = self.meme_contract.events.TokenCreated.process_receipt(
            receipt
        )
        if len(processed_logs) == 0:
            raise ValueError("Failed to create meme")

        token_address = processed_logs[0]["args"]["token"]

        def upload_when_safe():
            # Set a timeout of 5 minutes (300 seconds)
            start_time = time.time()
            timeout = 300

            while True:
                if time.time() - start_time > timeout:
                    logging.error("Timeout waiting for block to be safe")
                    break

                if (
                    self.w3.eth.get_block("safe").get("number", 0)
                    >= receipt["blockNumber"]
                ):
                    self._upload_meme_image(image_url)
                    break
                time.sleep(1)

        upload_thread = threading.Thread(target=upload_when_safe)
        upload_thread.daemon = True
        upload_thread.start()

        return token_address

    def _get_meme_list(self):
        response = requests.get(f"{self.confi_pump_helper_url}/api/getTokenList")
        response.raise_for_status()
        return response.json()
