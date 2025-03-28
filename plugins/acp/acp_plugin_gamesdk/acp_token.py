import asyncio
from enum import IntEnum
from time import time
from typing import Optional, Tuple, TypedDict, List
from datetime import datetime
from web3 import Web3
from eth_account import Account
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from .acp_token_abi import ACP_TOKEN_ABI

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
        network_url: str,
        contract_address: str = "0xd7beE7E06f0335721C919A3e5F35dDB4dD736127",
        virtuals_token_address: str = "0xbfAB80ccc15DF6fb7185f9498d6039317331846a"
    ):
        self.web3 = Web3(Web3.HTTPProvider(network_url))
        self.account = Account.from_key(wallet_private_key)
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.virtuals_token_address = Web3.to_checksum_address(virtuals_token_address)
        self.contract = self.web3.eth.contract(
            address=self.contract_address,
            abi=ACP_TOKEN_ABI
        )
        
    def get_contract_address(self) -> str:
        return self.contract_address

    def get_wallet_address(self) -> str:
        return self.account.address

    def create_job(
        self,
        provider_address: str,
        expire_at: datetime
    ) -> dict:
        try:
            provider_address = Web3.to_checksum_address(provider_address)
            expire_timestamp = int(expire_at.timestamp())
            
            transaction = self.contract.functions.createJob(
                provider_address,
                expire_timestamp
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction, 
                self.account.key
            )
            
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get job ID from event logs
            job_created_event = self.contract.events.JobCreated().process_receipt(receipt)
            job_id = job_created_event[0]['args']['jobId']
            
            return {
                'txHash': tx_hash.hex(),
                'jobId': job_id
            }
        except Exception as error:
            print(f"Error creating job: {error}")
            raise Exception("Failed to create job")

    def approve_allowance(self, price_in_wei: int) -> str:
        try:
            erc20_contract = self.web3.eth.contract(
                address=self.virtuals_token_address,
                abi=[{
                    "inputs": [
                        {"name": "spender", "type": "address"},
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }]
            )
            
            transaction = erc20_contract.functions.approve(
                self.contract_address,
                price_in_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction,
                self.account.key
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return tx_hash.hex()
        except Exception as error:
            print(f"Error approving allowance: {error}")
            raise Exception("Failed to approve allowance")

    def create_memo(
        self,
        job_id: int,
        content: str,
        memo_type: MemoType,
        is_secured: bool,
        next_phase: int
    ) -> dict:
        retries = 3
        while retries > 0:
            try:
                transaction = self.contract.functions.createMemo(
                    jobId = job_id,
                    content = content,
                    memoType = memo_type,
                    isSecured = is_secured,
                    nextPhase = next_phase
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': self.web3.eth.get_transaction_count(self.account.address),
                })
                
                signed_txn = self.web3.eth.account.sign_transaction(
                    transaction,
                    self.account.key
                )
                tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
                # Get memo ID from event logs
                new_memo_event = self.contract.events.NewMemo().process_receipt(receipt)
                memo_id = new_memo_event[0]['args']['memoId']
                
                return {
                    'txHash': tx_hash.hex(),
                    'memoId': memo_id
                }
            except Exception as error:
                print(f"Error creating memo: {error}")
                retries -= 1
                asyncio.sleep(2 * (3 - retries))
                
        raise Exception("Failed to create memo")

    def sign_memo(
        self,
        memo_id: int,
        is_approved: bool,
        reason: Optional[str] = ""
    ) -> str:
        retries = 3
        while retries > 0:
            try:
                transaction = self.contract.functions.signMemo(
                    memo_id,
                    is_approved,
                    reason or ""
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': self.web3.eth.get_transaction_count(self.account.address),
                })
                
                signed_txn = self.web3.eth.account.sign_transaction(
                    transaction,
                    self.account.key
                )
                
                tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
                self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
                return tx_hash.hex()
            except Exception as error:
                print(f"Error signing memo: {error}")
                retries -= 1
                asyncio.sleep(2 * (3 - retries))
                
        raise Exception("Failed to sign memo")

    def set_budget(self, job_id: int, budget: int) -> str:
        try:
            transaction = self.contract.functions.setBudget(
                job_id,
                budget
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction,
                self.account.key
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return tx_hash.hex()
        except Exception as error:
            print(f"Error setting budget: {error}")
            raise Exception("Failed to set budget")

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
            print(f"Error getting job: {error}")
            raise Exception("Failed to get job")

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
            print(f"Error getting memo: {error}")
            raise Exception("Failed to get memo")

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
            print(f"Error getting memos: {error}")
            raise Exception("Failed to get memos")
