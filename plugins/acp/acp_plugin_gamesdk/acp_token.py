from datetime import datetime
from enum import IntEnum
import json
import time
import traceback
from typing import Optional, Tuple, TypedDict

from eth_account import Account
from eth_account.messages import encode_defunct
import requests
from web3 import Web3

from acp_plugin_gamesdk.acp_token_abi import ACP_TOKEN_ABI
from acp_plugin_gamesdk.configs import ACPContractConfig


class MemoType(IntEnum):
    MESSAGE = 0
    CONTEXT_URL = 1
    IMAGE_URL = 2
    VOICE_URL = 3
    OBJECT_URL = 4
    TXHASH = 5


class IMemo(TypedDict):
    content: str
    memoType: MemoType
    isSecured: bool
    nextPhase: int
    jobId: int
    numApprovals: int
    sender: str


class IJob(TypedDict):
    id: int
    client: str
    provider: str
    budget: int
    amountClaimed: int
    phase: int
    memoCount: int
    expiredAt: int
    evaluatorCount: int


JobResult = Tuple[int, str, str, str, str, str, str, str, int]


class AcpToken:
    def __init__(
            self,
            wallet_private_key: str,
            agent_wallet_address: str,
            config: ACPContractConfig,
    ):
        self.web3 = Web3(Web3.HTTPProvider(config.rpc_url))
        self.account = Account.from_key(wallet_private_key)
        self.agent_wallet_address = agent_wallet_address
        self.contract_address = Web3.to_checksum_address(config.contract_address)
        self.virtuals_token_address = Web3.to_checksum_address(config.virtuals_token_address)
        self.contract = self.web3.eth.contract(
            address=self.contract_address,
            abi=ACP_TOKEN_ABI
        )
        self.virtuals_token_contract = self.web3.eth.contract(
            address=self.virtuals_token_address,
            abi=[{
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "spender",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "amount",
                        "type": "uint256"
                    }
                ],
                "name": "approve",
                "outputs": [
                    {
                        "internalType": "bool",
                        "name": "",
                        "type": "bool"
                    }
                ],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
        )
        self.acp_base_url = config.acp_api_url
        self.game_api_url = config.game_api_url
        self.chain_id = config.chain_id

    def get_agent_wallet_address(self) -> str:
        return self.agent_wallet_address

    def get_contract_address(self) -> str:
        return self.contract_address

    def validate_transaction(self, hash_value: str) -> object:
        try:
            response = requests.post(f"{self.acp_base_url}/acp-agent-wallets/trx-result",
                                     json={"userOpHash": hash_value})
            return response.json()
        except Exception as error:
            print(traceback.format_exc())
            raise Exception(f"Failed to get job_id {error}")

    def create_job(
            self,
            provider_address: str,
            evaluator_address: str,
            expire_at: datetime
    ) -> dict:
        try:
            provider_address = Web3.to_checksum_address(provider_address)
            evaluator_address = Web3.to_checksum_address(evaluator_address)
            expire_timestamp = int(expire_at.timestamp())

            # Sign the transaction
            trx_data, signature = self._sign_transaction(
                "createJob",
                [provider_address, evaluator_address, expire_timestamp]
            )

            # Prepare payload
            payload = {
                "agentWallet": self.get_agent_wallet_address(),
                "trxData": trx_data,
                "signature": signature
            }

            # Submit to custom API
            api_url = f"{self.acp_base_url}/acp-agent-wallets/transactions"
            response = requests.post(api_url, json=payload)

            if response.json().get("error"):
                raise Exception(
                    f"Failed to create job {response.json().get('error').get('status')}, Message: {response.json().get('error').get('message')}")

            # Return transaction hash or response ID
            return {"txHash": response.json().get("data", {}).get("userOpHash", "")}

        except Exception as e:
            raise

    def approve_allowance(self, price_in_wei: int) -> str:
        try:
            trx_data, signature = self._sign_transaction(
                "approve",
                [self.contract_address, price_in_wei],
                self.virtuals_token_address
            )

            payload = {
                "agentWallet": self.get_agent_wallet_address(),
                "trxData": trx_data,
                "signature": signature
            }

            api_url = f"{self.acp_base_url}/acp-agent-wallets/transactions"
            response = requests.post(api_url, json=payload)

            if (response.json().get("error")):
                raise Exception(
                    f"Failed to approve allowance {response.json().get('error').get('status')}, Message: {response.json().get('error').get('message')}")

            return response.json()
        except Exception as e:
            print(f"An error occurred while approving allowance: {e}")
            raise

    def create_memo(
            self,
            job_id: int,
            content: str,
            memo_type: MemoType,
            is_secured: bool,
            next_phase: int
    ) -> dict:
        retries = 3
        error = None
        while retries > 0:
            try:
                trx_data, signature = self._sign_transaction(
                    "createMemo",
                    [job_id, content, memo_type, is_secured, next_phase]
                )

                payload = {
                    "agentWallet": self.get_agent_wallet_address(),
                    "trxData": trx_data,
                    "signature": signature
                }

                api_url = f"{self.acp_base_url}/acp-agent-wallets/transactions"
                response = requests.post(api_url, json=payload)

                if (response.json().get("error")):
                    raise Exception(
                        f"Failed to create memo {response.json().get('error').get('status')}, Message: {response.json().get('error').get('message')}")

                return {"txHash": response.json().get("txHash", response.json().get("id", "")),
                        "memoId": response.json().get("memoId", "")}
            except Exception as e:
                print(f"{e}")
                print(traceback.format_exc())
                error = e
                retries -= 1
                time.sleep(2 * (3 - retries))

            if error:
                raise Exception(f"{error}")

    def _sign_transaction(self, method_name: str, args: list, contract_address: Optional[str] = None) -> Tuple[
        dict, str]:
        if contract_address:
            encoded_data = self.virtuals_token_contract.encode_abi(method_name, args=args)
        else:
            encoded_data = self.contract.encode_abi(method_name, args=args)

        trx_data = {
            "target": contract_address if contract_address else self.get_contract_address(),
            "value": "0",
            "data": encoded_data
        }

        message_json = json.dumps(trx_data, separators=(",", ":"), sort_keys=False)
        message_bytes = message_json.encode()

        # Sign the transaction
        message = encode_defunct(message_bytes)
        signature = "0x" + self.account.sign_message(message).signature.hex()

        return trx_data, signature

    def sign_memo(
            self,
            memo_id: int,
            is_approved: bool,
            reason: Optional[str] = ""
    ) -> str:
        retries = 3
        error = None
        while retries > 0:
            try:
                trx_data, signature = self._sign_transaction(
                    "signMemo",
                    [memo_id, is_approved, reason]
                )

                payload = {
                    "agentWallet": self.get_agent_wallet_address(),
                    "trxData": trx_data,
                    "signature": signature
                }

                api_url = f"{self.acp_base_url}/acp-agent-wallets/transactions"
                response = requests.post(api_url, json=payload)

                if (response.json().get("error")):
                    raise Exception(
                        f"Failed to sign memo {response.json().get('error').get('status')}, Message: {response.json().get('error').get('message')}")

                return response.json()

            except Exception as e:
                error = e
                print(f"{error}")
                print(traceback.format_exc())
                retries -= 1
                time.sleep(2 * (3 - retries))

        raise Exception(f"Failed to sign memo {error}")

    def set_budget(self, job_id: int, budget: int) -> str:
        try:
            trx_data, signature = self._sign_transaction(
                "setBudget",
                [job_id, budget]
            )

            payload = {
                "agentWallet": self.get_agent_wallet_address(),
                "trxData": trx_data,
                "signature": signature
            }

            api_url = f"{self.acp_base_url}/acp-agent-wallets/transactions"
            response = requests.post(api_url, json=payload)

            if (response.json().get("error")):
                raise Exception(
                    f"Failed to set budget {response.json().get('error').get('status')}, Message: {response.json().get('error').get('message')}")

            return response.json()
        except Exception as error:
            raise Exception(f"{error}")

    def get_job(self, job_id: int) -> Optional[IJob]:
        try:
            job_data = self.contract.functions.jobs(job_id).call()

            if not job_data:
                return None

            return {
                'id': job_data[0],
                'client': job_data[1],
                'provider': job_data[2],
                'budget': int(job_data[3]),
                'amountClaimed': int(job_data[4]),
                'phase': int(job_data[5]),
                'memoCount': int(job_data[6]),
                'expiredAt': int(job_data[7]),
                'evaluatorCount': int(job_data[8])
            }
        except Exception as error:
            raise Exception(f"{error}")

    def get_memo_by_job(
            self,
            job_id: int,
            memo_type: Optional[MemoType] = None
    ) -> Optional[IMemo]:
        try:
            memos = self.contract.functions.getAllMemos(job_id).call()

            if memo_type is not None:
                filtered_memos = [m for m in memos if m['memoType'] == memo_type]
                return filtered_memos[-1] if filtered_memos else None
            else:
                return memos[-1] if memos else None
        except Exception as error:
            raise Exception(f"Failed to get memo by job {error}")

    def get_memos_for_phase(
            self,
            job_id: int,
            phase: int,
            target_phase: int
    ) -> Optional[IMemo]:
        try:
            memos = self.contract.functions.getMemosForPhase(job_id, phase).call()

            target_memos = [m for m in memos if m['nextPhase'] == target_phase]
            return target_memos[-1] if target_memos else None
        except Exception as error:
            raise Exception(f"Failed to get memos for phase {error}")
