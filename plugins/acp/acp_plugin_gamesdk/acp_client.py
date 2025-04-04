from datetime import datetime, timedelta
from typing import List, Optional
from web3 import Web3
import requests

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from .interface import AcpAgent, AcpJobPhases, AcpState
from .acp_token import AcpToken, MemoType

class AcpClient:
    def __init__(self, api_key: str, acp_token: AcpToken):
        self.base_url = "https://sdk-dev.game.virtuals.io/acp"
        self.api_key = api_key
        self.acp_token = acp_token
        self.web3 = Web3()

    @property
    def wallet_address(self) -> str:
        return self.acp_token.get_wallet_address()
    
    @property
    
    def agent_wallet_address(self) -> str:
        return self.acp_token.get_agent_wallet_address()

    def get_state(self) -> AcpState:
        response =  requests.get(
            f"{self.base_url}/states/{self.wallet_address}",
            headers={"x-api-key": self.api_key}
        )
        return response.json()

    def browse_agents(self, cluster: Optional[str] = None) -> List[AcpAgent]:
        url = "https://acpx.virtuals.gg/api/agents"
        
        params = {}
        if cluster:
            params["filters[cluster]"] = cluster
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Failed to browse agents: {response.text}")

        response_json = response.json()
        
        return [
            {
                "id": agent["id"],
                "name": agent["name"],
                "description": agent["description"],
                "walletAddress": agent["walletAddress"]
            }
            for agent in response_json.get("data", [])
        ]

    def create_job(self, provider_address: str, price: float, job_description: str) -> int:
        expire_at = datetime.now() + timedelta(days=1)
        
        tx_result =  self.acp_token.create_job(
            provider_address=provider_address,
            expire_at=expire_at
        )
        job_id = tx_result["jobId"]
        memo_response =  self.acp_token.create_memo(
            job_id=job_id,
            content=job_description,
            memo_type=MemoType.MESSAGE,
            is_secured=False,
            next_phase=AcpJobPhases.NEGOTIATION
        )

        payload = {
            "jobId": job_id,
            "clientAddress": self.acp_token.get_wallet_address(),
            "providerAddress": provider_address,
            "description": job_description,
            "price": price,
            "expiredAt": expire_at.isoformat()
        }

        requests.post(
            self.base_url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "x-api-key": self.api_key
            }
        )

        return job_id

    def response_job(self, job_id: int, accept: bool, memo_id: int, reasoning: str):
        if accept:
            tx_hash = self.acp_token.sign_memo(memo_id, accept, reasoning)
            
            return self.acp_token.create_memo(
                job_id=job_id,
                content=f"Job {job_id} accepted. {reasoning}",
                memo_type=MemoType.MESSAGE,
                is_secured=False,
                next_phase=AcpJobPhases.TRANSACTION
            )
        else:
            return self.acp_token.create_memo(
                job_id=job_id,
                content=f"Job {job_id} rejected. {reasoning}",
                memo_type=MemoType.MESSAGE,
                is_secured=False,
                next_phase=AcpJobPhases.REJECTED
            )

    def make_payment(self, job_id: int, amount: float, memo_id: int, reason: str):
        # Convert amount to Wei (smallest ETH unit)
        amount_wei = self.web3.to_wei(amount, 'ether')
        
        tx_hash = self.acp_token.set_budget(job_id, amount_wei)
        approval_tx_hash = self.acp_token.approve_allowance(amount_wei)
        return self.acp_token.sign_memo(memo_id, True, reason)

    def deliver_job(self, job_id: int, deliverable: str, memo_id: int, reason: str):
        return self.acp_token.create_memo(
            job_id=job_id,
            content=deliverable,
            memo_type=MemoType.MESSAGE,
            is_secured=False,
            next_phase=AcpJobPhases.COMPLETED
        )

    def add_tweet(self, job_id: int, tweet_id: str, content: str):
        """
        Add a tweet to a job.
        
        Args:
            job_id: The ID of the job
            tweet_id: The ID of the tweet
            content: The content of the tweet
        
        Raises:
            Exception: If the request fails
        """
        payload = {
            "tweetId": tweet_id,
            "content": content
        }
        
        response = requests.post(
            f"{self.base_url}/{job_id}/tweets/{self.wallet_address}",
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "x-api-key": self.api_key
            }
        )
        
        if response.status_code != 200 and response.status_code != 201:
            raise Exception(f"Failed to add tweet: {response.status_code} {response.text}")
        
        
        return response.json()
    
    def reset_state(self, wallet_address: str ) -> None:
        if not wallet_address:
            raise Exception("Wallet address is required")
        
        address = wallet_address
        
        response = requests.delete(
            f"{self.base_url}/states/{address}",
            headers={"x-api-key": self.api_key}
        )
        
        if response.status_code not in [200, 204]:
            raise Exception(f"Failed to reset state: {response.status_code} {response.text}")
