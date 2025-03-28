from typing import List, Dict, Any, Optional,Tuple
import json
from dataclasses import dataclass
from datetime import datetime

from game_sdk.game.agent import WorkerConfig
from game_sdk.game.custom_types import Function, FunctionResultStatus
from plugins.twitter.twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin

import sys
import os
from plugins.acp.acp_plugin_gamesdk import acp_client
from plugins.twitter.twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
from plugins.twitter.twitter_plugin_gamesdk.game_twitter_plugin import GameTwitterPlugin
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from .acp_client import AcpClient
from .acp_token import AcpToken
from .interface import AcpJobPhasesDesc, IInventory

@dataclass
class AdNetworkPluginOptions:
    api_key: str
    acp_token_client: AcpToken
    twitter_plugin: TwitterPlugin | GameTwitterPlugin = None
    cluster: Optional[str] = None

class AcpPlugin:
    def __init__(self, options: AdNetworkPluginOptions):
        print("Initializing AcpPlugin")
        self.acp_client = AcpClient(options.api_key, options.acp_token_client)
        
        self.id = "acp_worker"
        self.name = "ACP Worker"
        self.description = """
        Handles trading transactions and jobs between agents. This worker ONLY manages:

        1. RESPONDING to Buy/Sell Needs
          - Find sellers when YOU need to buy something
          - Handle incoming purchase requests when others want to buy from YOU
          - NO prospecting or client finding

        2. Job Management
          - Process purchase requests. Accept or reject job.
          - Send payments
          - Manage and deliver services and goods

        NOTE: This is NOT for finding clients - only for executing trades when there's a specific need to buy or sell something.
        """
        self.cluster = options.cluster
        self.twitter_plugin = options.twitter_plugin
        self.produced_inventory: List[IInventory] = []

    def add_produce_item(self, item: IInventory) -> None:
        self.produced_inventory.append(item)

    def get_acp_state(self) -> Dict:
        server_state = self.acp_client.get_state()
        server_state["inventory"]["produced"] = self.produced_inventory
        return server_state

    def get_worker(self, data: Optional[Dict] = None) -> WorkerConfig:
        functions = data.get("functions") if data else [
            self.search_agents_functions,
            self.initiate_job,
            self.respond_job,
            self.pay_job,
            self.deliver_job,
        ]
        
        def get_environment(_e, __) -> Dict[str, Any]:
            environment = data.get_environment() if hasattr(data, "get_environment") else {}
            return {
                **environment,
                **(self.get_acp_state()),
            }

        data = WorkerConfig(
            id=self.id,
            worker_description=self.description,
            action_space=functions,
            get_state_fn=get_environment,
            instruction=data.get("instructions") if data else None
        )
        
        return data

    @property
    def agent_description(self) -> str:
        return """
        Inventory structure
          - inventory.aquired: Deliverable that your have bought and can be use to achived your objective
          - inventory.produced: Deliverable that needs to be delivered to your seller

        Job Structure:
          - jobs.active:
            * asABuyer: Pending resource purchases
            * asASeller: Pending design requests
          - jobs.completed: Successfully fulfilled projects
          - jobs.cancelled: Terminated or rejected requests
          - Each job tracks:
            * phase: request (seller should response to accept/reject to the job) → pending_payment (as a buyer to make the payment for the service) → in_progress (seller to deliver the service) → evaluation → completed/rejected
        """
        
    def _search_agents_executable(self,reasoning: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not reasoning:
            return FunctionResultStatus.FAILED, "Reasoning for the search must be provided. This helps track your decision-making process for future reference.", {}
            
        agents = self.acp_client.browse_agents(self.cluster)
        
        if not agents:
            return FunctionResultStatus.FAILED, "No other trading agents found in the system. Please try again later when more agents are available.", {}
            
        return FunctionResultStatus.DONE, json.dumps({
            "availableAgents": agents,
            "totalAgentsFound": len(agents),
            "timestamp": datetime.now().timestamp(),
            "note": "Use the walletAddress when initiating a job with your chosen trading partner."
        }), {}

    @property
    def search_agents_functions(self) -> Function:
        return Function(
            fn_name="search_agents",
            fn_description="Get a list of all available trading agents and what they're selling. Use this function before initiating a job to discover potential trading partners. Each agent's entry will show their ID, name, type, walletAddress, description and product catalog with prices.",
            args=[
                {
                    "name": "reasoning",
                    "type": "string",
                    "description": "Explain why you need to find trading partners at this time",
                }
            ],
            executable=self._search_agents_executable
        )

    @property
    def initiate_job(self) -> Function:
        return Function(
            fn_name="initiate_job",
            fn_description="Creates a purchase request for items from another agent's catalog. Only for use when YOU are the buyer. The seller must accept your request before you can proceed with payment.",
            args=[
                {
                    "name": "sellerWalletAddress",
                    "type": "string",
                    "description": "The seller's agent wallet address you want to buy from",
                },
                {
                    "name": "price",
                    "type": "string",
                    "description": "Offered price for service",
                },
                {
                    "name": "reasoning",
                    "type": "string",
                    "description": "Why you are making this purchase request",
                },
                {
                    "name": "serviceRequirements",
                    "type": "string",
                    "description": "Detailed specifications for service-based items",
                },
                {
                    "name": "tweetContent",
                    "type": "string",
                    "description": "Tweet content that will be posted about this job. Must include the seller's Twitter handle (with @ symbol) to notify them",
                },
            ],
            executable=self._initiate_job_executable
        )

    def _initiate_job_executable(self, sellerWalletAddress: str, price: str, reasoning: str, serviceRequirements: str, tweetContent : str) -> Tuple[FunctionResultStatus, str, dict]:
        if not price:
            return FunctionResultStatus.FAILED, "Missing price - specify how much you're offering per unit", {}

        try:
            state = self.get_acp_state()

            if state["jobs"]["active"]["asABuyer"]:
                return FunctionResultStatus.FAILED, "You already have an active job as a buyer", {}

            # ... Rest of validation logic ...
            
            job_id = self.acp_client.create_job(
                sellerWalletAddress,
                float(price),
                serviceRequirements
            )
            
            if (self.twitter_plugin is not None and tweetContent is not None):
                post_tweet_fn = self.twitter_plugin.get_function('post_tweet')
                tweet_id = post_tweet_fn(tweetContent, None).get('data', {}).get('id')
                if (tweet_id is not None):
                    self.acp_client.add_tweet(job_id,tweet_id, tweetContent)
                    print("Tweet has been posted")

            return FunctionResultStatus.DONE, json.dumps({
                "jobId": job_id,
                "sellerWalletAddress": sellerWalletAddress,
                "price": float(price),
                "serviceRequirements": serviceRequirements,
                "timestamp": datetime.now().timestamp(),
            }), {}
        except Exception as e:
            return FunctionResultStatus.FAILED, f"System error while initiating job - try again after a short delay. {str(e)}", {}

    @property
    def respond_job(self) -> Function:
        return Function(
            fn_name="respond_to_job",
            fn_description="Accepts or rejects an incoming 'request' job",
            args=[
                {
                    "name": "jobId",
                    "type": "string",
                    "description": "The job ID you are responding to",
                },
                {
                    "name": "decision",
                    "type": "string",
                    "description": "Your response: 'ACCEPT' or 'REJECT'",
                },
                {
                    "name": "reasoning",
                    "type": "string",
                    "description": "Why you made this decision",
                },
                {
                    "name": "tweetContent",
                    "type": "string",
                    "description": "Tweet content that will be posted about this job. Must include the seller's Twitter handle (with @ symbol) to notify them",
                },
            ],
            executable=self._respond_job_executable
        )

    def _respond_job_executable(self, jobId: str, decision: str, reasoning: str, tweetContent: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not jobId:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're responding to", {}
        
        if not decision or decision not in ["ACCEPT", "REJECT"]:
            return FunctionResultStatus.FAILED, "Invalid decision - must be either 'ACCEPT' or 'REJECT'", {}
            
        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you made this decision", {}

        try:
            state = self.get_acp_state()
            
            job = next(
                (c for c in state["jobs"]["active"]["asASeller"] if c["jobId"] == int(jobId)),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your seller jobs - check the ID and verify you're the seller", {}

            if job["phase"] != AcpJobPhasesDesc.REQUEST:
                return FunctionResultStatus.FAILED, f"Cannot respond - job is in '{job['phase']}' phase, must be in 'request' phase", {}

            self.acp_client.response_job(
                int(jobId),
                decision == "ACCEPT",
                job["memo"][0]["id"],
                reasoning
            )
            
            if (self.twitter_plugin is not None):
                tweet_history = job.get("tweetHistory", [])
                tweet_id = tweet_history[-1].get("tweetId") if tweet_history else None
                if (tweet_id is not None):
                    reply_tweet_fn = self.twitter_plugin.get_function('reply_tweet')
                    tweet_id = reply_tweet_fn(tweet_id,tweetContent, None).get('data', {}).get('id')
                    if (tweet_id is not None):
                        self.acp_client.add_tweet(jobId ,tweet_id, tweetContent)
                        print("Tweet has been posted")

            return FunctionResultStatus.DONE, json.dumps({
                "jobId": jobId,
                "decision": decision,
                "timestamp": datetime.now().timestamp()
            }), {}
        except Exception as e:
            return FunctionResultStatus.FAILED, f"System error while responding to job - try again after a short delay. {str(e)}", {}

    @property
    def pay_job(self) -> Function:
        return Function(
            fn_name="pay_job",
            fn_description="Processes payment for an accepted purchase request",
            args=[
                {
                    "name": "jobId",
                    "type": "number",
                    "description": "The job ID you are paying for",
                },
                {
                    "name": "amount",
                    "type": "number",
                    "description": "The total amount to pay",
                },
                {
                    "name": "reasoning",
                    "type": "string",
                    "description": "Why you are making this payment",
                },
                {
                    "name": "tweetContent",
                    "type": "string",
                    "description": "Tweet content that will be posted about this job. Must include the seller's Twitter handle (with @ symbol) to notify them",
                },
            ],
            executable=self._pay_job_executable
        )

    def _pay_job_executable(self, jobId: str, amount: str, reasoning: str, tweetContent: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not jobId:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're paying for", {}

        if not amount:
            return FunctionResultStatus.FAILED, "Missing amount - specify how much you're paying", {}

        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you're making this payment", {}

        try:
            state = self.get_acp_state()
            
            job = next(
                (c for c in state["jobs"]["active"]["asABuyer"] if c["jobId"] == int(jobId)),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your buyer jobs - check the ID and verify you're the buyer", {}

            if job["phase"] != AcpJobPhasesDesc.NEGOTIATION:
                return FunctionResultStatus.FAILED, f"Cannot pay - job is in '{job['phase']}' phase, must be in 'negotiation' phase", {}


            self.acp_client.make_payment(
                int(jobId),
                float(amount),
                job["memo"][0]["id"],
                reasoning
            )
            
            if (self.twitter_plugin is not None):
                tweet_history = job.get("tweetHistory", [])
                tweet_id = tweet_history[-1].get("tweetId") if tweet_history else None
                if (tweet_id is not None):
                    reply_tweet_fn = self.twitter_plugin.get_function('reply_tweet')
                    tweet_id = reply_tweet_fn(tweet_id,tweetContent, None).get('data', {}).get('id')
                    if (tweet_id is not None):
                        self.acp_client.add_tweet(jobId ,tweet_id, tweetContent)
                        print("Tweet has been posted")

            return FunctionResultStatus.DONE, json.dumps({
                "jobId": jobId,
                "amountPaid": amount,
                "timestamp": datetime.now().timestamp()
            }), {}
        except Exception as e:
            return FunctionResultStatus.FAILED, f"System error while processing payment - try again after a short delay. {str(e)}", {}

    @property
    def deliver_job(self) -> Function:
        return Function(
            fn_name="deliver_job",
            fn_description="Completes a sale by delivering items to the buyer",
            args=[
                {
                    "name": "jobId",
                    "type": "string",
                    "description": "The job ID you are delivering for",
                },
                {
                    "name": "deliverableType",
                    "type": "string",
                    "description": "Type of the deliverable",
                },
                {
                    "name": "deliverable",
                    "type": "string",
                    "description": "The deliverable item",
                },
                {
                    "name": "reasoning",
                    "type": "string",
                    "description": "Why you are making this delivery",
                },
                {
                    "name": "tweetContent",
                    "type": "string",
                    "description": "Tweet content that will be posted about this job. Must include the seller's Twitter handle (with @ symbol) to notify them",
                },
            ],
            executable=self._deliver_job_executable
        )

    def _deliver_job_executable(self, jobId: str, deliverableType: str, deliverable: str, reasoning: str, tweetContent: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not jobId:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're delivering for", {}
            
        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you're making this delivery", {}
            
        if not deliverable:
            return FunctionResultStatus.FAILED, "Missing deliverable - specify what you're delivering", {}

        try:
            state = self.get_acp_state()
            
            job = next(
                (c for c in state["jobs"]["active"]["asASeller"] if c["jobId"] == int(jobId)),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your seller jobs - check the ID and verify you're the seller", {}

            if job["phase"] != AcpJobPhasesDesc.TRANSACTION:
                return FunctionResultStatus.FAILED, f"Cannot deliver - job is in '{job['phase']}' phase, must be in 'transaction' phase", {}

            produced = next(
                (i for i in self.produced_inventory if i["jobId"] == job["jobId"]),
                None
            )

            if not produced:
                return FunctionResultStatus.FAILED, "Cannot deliver - you should be producing the deliverable first before delivering it", {}

            deliverable = {
                "type": deliverableType,
                "value": deliverable
            }

            self.acp_client.deliver_job(
                int(jobId),
                json.dumps(deliverable),
                job["memo"][0]["id"],
                reasoning
            )
            
            if (self.twitter_plugin is not None):
                tweet_history = job.get("tweetHistory", [])
                tweet_id = tweet_history[-1].get("tweetId") if tweet_history else None
                if (tweet_id is not None):
                    reply_tweet_fn = self.twitter_plugin.get_function('reply_tweet')
                    tweet_id = reply_tweet_fn(tweet_id,tweetContent, None).get('data', {}).get('id')
                    if (tweet_id is not None):
                        self.acp_client.add_tweet(jobId ,tweet_id, tweetContent)
                        print("Tweet has been posted")

            return FunctionResultStatus.DONE, json.dumps({
                "status": "success",
                "jobId": jobId,
                "deliverable": deliverable,
                "timestamp": datetime.now().timestamp()
            }), {}
        except Exception as e:
            return FunctionResultStatus.FAILED, f"System error while delivering items - try again after a short delay. {str(e)}", {}
