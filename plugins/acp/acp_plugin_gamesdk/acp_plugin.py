import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional,Tuple

import requests

from game_sdk.game.agent import WorkerConfig
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
from virtuals_acp import IDeliverable
from virtuals_acp.models import ACPGraduationStatus, ACPOnlineStatus

from acp_plugin_gamesdk.interface import AcpJobPhasesDesc, IInventory, ACP_JOB_PHASE_MAP
from virtuals_acp.client import VirtualsACP 
from virtuals_acp.job import ACPJob

@dataclass
class AcpPluginOptions:
    api_key: str
    acp_client: VirtualsACP  
    twitter_plugin: TwitterPlugin | None = None
    cluster: Optional[str] = None
    evaluator_cluster: Optional[str] = None
    graduation_status: Optional[ACPGraduationStatus] = None
    online_status: Optional[ACPOnlineStatus] = None
    job_expiry_duration_mins: Optional[int] = None
    keep_completed_jobs: Optional[int] = None
    keep_cancelled_jobs: Optional[int] = None
    keep_produced_inventory: Optional[int] = None
    
class AcpPlugin:
    def __init__(self, options: AcpPluginOptions):
        print("Initializing AcpPlugin")
        self.acp_client = options.acp_client
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
        self.evaluator_cluster = options.evaluator_cluster
        self.graduation_status = options.graduation_status
        self.online_status = options.online_status
        self.twitter_plugin = None
        if options.twitter_plugin is not None:
            self.twitter_plugin = options.twitter_plugin
            
        self.produced_inventory: List[IInventory] = []
        self.acp_base_url = self.acp_client.acp_api_url
        self.job_expiry_duration_mins = options.job_expiry_duration_mins if options.job_expiry_duration_mins is not None else 1440
        self.keep_completed_jobs = options.keep_completed_jobs if options.keep_completed_jobs is not None else 1
        self.keep_cancelled_jobs = options.keep_cancelled_jobs if options.keep_cancelled_jobs is not None else 0
        self.keep_produced_inventory = options.keep_produced_inventory if options.keep_produced_inventory is not None else 1

        
    def add_produce_item(self, item: IInventory) -> None:
        self.produced_inventory.append(item)

    def get_acp_state(self) -> Dict:
        agent_addr = self.acp_client.agent_address.lower()

        def serialize_job(job: ACPJob, active: bool) -> Dict:
            return {
                "job_id": job.id,
                "client_name": job.client_agent.name if job.client_agent else "",
                "provider_name": job.provider_agent.name if job.provider_agent else "",
                "desc": job.service_requirement or "",
                "price": str(job.price),
                "provider_address": job.provider_address,
                "phase": ACP_JOB_PHASE_MAP.get(job.phase),
                # Include memos only if active
                "memo": [
                    {
                        "id": m.id,
                        "type": m.type.value,
                        "content": m.content,
                        "next_phase": m.next_phase.value,
                    }
                    for m in reversed(job.memos)
                ] if active and job.memos else [],
                # Include tweet_history only if active
                "tweet_history": [
                    {
                        "type": t.get("type"),
                        "tweet_id": t.get("tweetId"),
                        "content": t.get("content"),
                        "created_at": t.get("createdAt"),
                    }
                    for t in reversed(job.context.get("tweets", []))
                ] if active and job.context else [],
            }

        # Fetch job states
        active_jobs = self.acp_client.get_active_jobs()

        # Fetch completed jobs if not explicitly disabled
        if self.keep_completed_jobs == 0:
            completed_jobs = []
        else:
            completed_jobs = self.acp_client.get_completed_jobs()

        # Fetch cancelled jobs if not explicitly disabled
        if self.keep_cancelled_jobs == 0:
            cancelled_jobs = []
        else:
            cancelled_jobs = self.acp_client.get_cancelled_jobs()

        active_buyer_jobs = [
            serialize_job(job, active=True)
            for job in active_jobs
            if job.client_address.lower() == agent_addr
        ]

        active_seller_jobs = [
            serialize_job(job, active=True)
            for job in active_jobs
            if job.provider_address.lower() == agent_addr
        ]

        # Limit completed and cancelled jobs
        completed = [
            serialize_job(job, active=False)
            for job in (
                completed_jobs[:self.keep_completed_jobs]
                if self.keep_completed_jobs is not None
                else completed_jobs
            )
        ]

        cancelled = [
            serialize_job(job, active=False)
            for job in (
                cancelled_jobs[:self.keep_cancelled_jobs]
                if self.keep_cancelled_jobs is not None
                else cancelled_jobs
            )
        ]

        # Produced inventory logic
        produced = []
        if self.produced_inventory and self.keep_produced_inventory > 0:
            produced = [
                item.model_dump() for item in (
                    self.produced_inventory[:self.keep_produced_inventory]
                    if self.keep_produced_inventory is not None
                    else self.produced_inventory
                )
            ]

        return {
            "inventory": {
                "acquired": [],
                "produced": produced,
            },
            "jobs": {
                "active": {
                    "as_a_buyer": active_buyer_jobs,
                    "as_a_seller": active_seller_jobs,
                },
                "completed": completed,
                "cancelled": cancelled,
            },
        }

    def get_worker(self, data: Optional[Dict] = None) -> WorkerConfig:
        functions = data.get("functions") if data else [
            self.search_agents_functions,
            self.initiate_job,
            self.respond_job,
            self.pay_job,
            self.deliver_job,
        ]
        
        def get_environment(_function_result, _current_state) -> Dict[str, Any]:
            environment = data.get_environment() if hasattr(data, "get_environment") else {}
            return {
                **environment,
                **(self.get_acp_state()),
            }

        worker_config = WorkerConfig(
            id=self.id,
            worker_description=self.description,
            action_space=functions,
            get_state_fn=get_environment,
            instruction=data.get("instructions") if data else None
        )
        
        return worker_config

    @property
    def agent_description(self) -> str:
        return """
        Inventory structure
          - inventory.aquired: Deliverable that your have bought and can be use to achived your objective
          - inventory.produced: Deliverable that needs to be delivered to your seller

        Job Structure:
          - jobs.active:
            * as_a_buyer: Pending resource purchases
            * as_a_seller: Pending design requests
          - jobs.completed: Successfully fulfilled projects
          - jobs.cancelled: Terminated or rejected requests
          - Each job tracks:
            * phase: request (seller should response to accept/reject to the job) → pending_payment (as a buyer to make the payment for the service) → in_progress (seller to deliver the service) → evaluation → completed/rejected
        """
        
    def _search_agents_executable(self, reasoning: str, keyword: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not reasoning:
            return FunctionResultStatus.FAILED, "Reasoning for the search must be provided. This helps track your decision-making process for future reference.", {}

        agents = self.acp_client.browse_agents(keyword, self.cluster, graduation_status=self.graduation_status, online_status=self.online_status)

        if not agents:
            return FunctionResultStatus.FAILED, "No other trading agents found in the system. Please try again later when more agents are available.", {}

        return (
            FunctionResultStatus.DONE,
            json.dumps(
                {
                    "availableAgents": [
                        {
                            "id": agent.id,
                            "name": agent.name,
                            "twitter_handle": agent.twitter_handle,
                            "description": agent.description,
                            "wallet_address": agent.wallet_address,
                            "offerings": (
                                [
                                    {"name": offering.type, "price": offering.price}
                                    for offering in agent.offerings
                                ]
                                if agent.offerings
                                else []
                            ),
                        }
                        for agent in agents
                    ],
                    "totalAgentsFound": len(agents),
                    "timestamp": datetime.now().timestamp(),
                    "note": "Use the wallet_address when initiating a job with your chosen trading partner.",
                }
            ),
            {},
        )

    @property
    def search_agents_functions(self) -> Function:
        reasoning_arg = Argument(
            name="reasoning",
            type="string",
            description="Explain why you need to find trading partners at this time",
        )

        keyword_arg = Argument(
            name="keyword",
            type="string",
            description="Search for agents by name or description. Use this to find specific trading partners or products.",
        )

        return Function(
            fn_name="search_agents",
            fn_description="Get a list of all available trading agents and what they're selling. Use this function before initiating a job to discover potential trading partners. Each agent's entry will show their ID, name, type, walletAddress, description and product catalog with prices.",
            args=[reasoning_arg, keyword_arg],
            executable=self._search_agents_executable
        )

    @property
    def initiate_job(self) -> Function:
        seller_wallet_address_arg = Argument(
            name="seller_wallet_address",
            type="string",
            description="The seller's agent wallet address you want to buy from",
        )

        price_arg = Argument(
            name="price",
            type="string",
            description="Offered price for service",
        )

        reasoning_arg = Argument(
            name="reasoning",
            type="string",
            description="Why you are making this purchase request",
        )

        service_requirements_arg = Argument(
            name="service_requirements",
            type="string",
            description="Detailed specifications for service-based items",
        )
        
        require_evaluation_arg = Argument(
            name="require_evaluation",
            type="boolean",
            description="Decide if your job request is complex enough to spend money for evaluator agent to assess the relevancy of the output. For simple job request like generate image, insights, facts does not require evaluation. For complex and high level job like generating a promotion video, a marketing narrative, a trading signal should require evaluator to assess result relevancy.",
        )
        
        evaluator_keyword_arg = Argument(
            name="evaluator_keyword",
            type="string",
            description="Keyword to search for a evaluator",
        )

        args = [seller_wallet_address_arg, price_arg, reasoning_arg, service_requirements_arg, require_evaluation_arg, evaluator_keyword_arg]
        
        if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None:
            tweet_content_arg = Argument(
                name="tweet_content",
                type="string",
                description="Tweet content that will be posted about this job. Must include the seller's Twitter handle (with @ symbol) to notify them",
            )
            args.append(tweet_content_arg)
            
        return Function(
            fn_name="initiate_job",
            fn_description="Creates a purchase request for items from another agent's catalog. Only for use when YOU are the buyer. The seller must accept your request before you can proceed with payment.",
            args=args,
            executable=self._initiate_job_executable
        )

    def _initiate_job_executable(self, seller_wallet_address: str, price: str, reasoning: str, service_requirements: str, require_evaluation: str, evaluator_keyword: str, tweet_content: Optional[str] = None) -> Tuple[FunctionResultStatus, str, dict]:
        if isinstance(require_evaluation, str):
            require_evaluation = require_evaluation.lower() == 'true'
        elif isinstance(require_evaluation, bool):
            require_evaluation = require_evaluation
        else:
            require_evaluation = False

        if not price:
            return FunctionResultStatus.FAILED, "Missing price - specify how much you're offering per unit", {}
        
        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you're making this purchase request", {}
        
        try:
            if not seller_wallet_address:
                return FunctionResultStatus.FAILED, "Missing seller wallet address - specify the agent you want to buy from", {}
            
            if require_evaluation and not evaluator_keyword:
                return FunctionResultStatus.FAILED, "Missing validator keyword - provide a keyword to search for a validator", {}
            
            evaluator_address = self.acp_client.agent_address
            
            if require_evaluation:
                validators = self.acp_client.browse_agents(evaluator_keyword, self.evaluator_cluster, graduation_status=self.graduation_status, online_status=self.online_status)
                
                if len(validators) == 0:
                    return FunctionResultStatus.FAILED, "No evaluator found - try a different keyword", {}

                evaluator_address = validators[0].wallet_address
            
            expired_at = datetime.now(timezone.utc) + timedelta(minutes=self.job_expiry_duration_mins)
            job_id = self.acp_client.initiate_job(
                seller_wallet_address,
                service_requirements,
                float(price),
                evaluator_address,
                expired_at
            )

            if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None and tweet_content is not None:
                self._tweet_job(job_id, f"{tweet_content} #{job_id}")

            return FunctionResultStatus.DONE, json.dumps({
                "job_id": job_id,
                "seller_wallet_address": seller_wallet_address,
                "price": float(price),
                "service_requirements": service_requirements,
                "timestamp": datetime.now().timestamp(),
            }), {}
        except Exception as e:
            print(traceback.format_exc())
            return FunctionResultStatus.FAILED, f"System error while initiating job - try again after a short delay. {str(e)}", {}

    @property
    def respond_job(self) -> Function:
        job_id_arg = Argument(
            name="job_id",
            type="integer",
            description="The job ID you are responding to",
        )

        decision_arg = Argument(
            name="decision",
            type="string",
            description="Your response: 'ACCEPT' or 'REJECT'",
        )

        reasoning_arg = Argument(
            name="reasoning",
            type="string",
            description="Why you made this decision",
        )
        
        args = [job_id_arg, decision_arg, reasoning_arg]
        
        if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None:
            tweet_content_arg = Argument(
                name="tweet_content",
                type="string",
                description="Tweet content about your decision for the specific job. MUST NOT TAG THE BUYER. This is to avoid spamming the buyer's feed with your decision.",
            )
            args.append(tweet_content_arg)

        return Function(
            fn_name="respond_to_job",
            fn_description="Accepts or rejects an incoming 'request' job",
            args=args,
            executable=self._respond_job_executable
        )

    def _respond_job_executable(self, job_id: int, decision: str, reasoning: str, tweet_content: Optional[str] = None) -> Tuple[FunctionResultStatus, str, dict]:
        if not job_id:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're responding to", {}
        
        if not decision or decision not in ["ACCEPT", "REJECT"]:
            return FunctionResultStatus.FAILED, "Invalid decision - must be either 'ACCEPT' or 'REJECT'", {}
            
        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you made this decision", {}

        try:
            state = self.get_acp_state()
            
            # Check if job is cancelled
            if any(c["jobId"] == jobId for c in state["jobs"]["cancelled"]):
                return FunctionResultStatus.FAILED, "Cannot respond - this job has been cancelled", {}
            
            job = next(
                (c for c in state["jobs"]["active"]["as_a_seller"] if c["job_id"] == job_id),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your seller jobs - check the ID and verify you're the seller", {}

            if job["phase"] != AcpJobPhasesDesc.REQUEST:
                return FunctionResultStatus.FAILED, f"Cannot respond - job is in '{job['phase']}' phase, must be in 'request' phase", {}

            self.acp_client.respond_to_job_memo(
                job_id,
                job["memo"][0]["id"],
                decision == "ACCEPT",
                reasoning
            )

            if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None and tweet_content is not None:
                tweet_id = job.get("tweet_history", [])[0].get("tweet_id") if job.get("tweet_history") else None
                if tweet_id:
                    self._tweet_job(job_id, tweet_content, tweet_id)

            return FunctionResultStatus.DONE, json.dumps({
                "job_id": job_id,
                "decision": decision,
                "timestamp": datetime.now().timestamp()
            }), {}
        except Exception as e:
            return FunctionResultStatus.FAILED, f"System error while responding to job - try again after a short delay. {str(e)}", {}

    @property
    def pay_job(self) -> Function:
        job_id_arg = Argument(
            name="job_id",
            type="integer",
            description="The job ID you are paying for",
        )

        amount_arg = Argument(
            name="amount",
            type="float",
            description="The total amount to pay",  # in Ether
        )

        reasoning_arg = Argument(
            name="reasoning",
            type="string",
            description="Why you are making this payment",
        )

        args = [job_id_arg, amount_arg, reasoning_arg]
        
        if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None:
            tweet_content_arg = Argument(
                name="tweet_content",
                type="string",
                description="Tweet content about your payment for the specific job. MUST NOT TAG THE BUYER. This is to avoid spamming the buyer's feed with your payment.",
            )
            args.append(tweet_content_arg)

        return Function(
            fn_name="pay_job",
            fn_description="Processes payment for an accepted purchase request",
            args=args,
            executable=self._pay_job_executable
        )

    def _pay_job_executable(self, job_id: int, amount: float, reasoning: str, tweet_content: Optional[str] = None) -> Tuple[FunctionResultStatus, str, dict]:
        if not job_id:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're paying for", {}

        if not amount:
            return FunctionResultStatus.FAILED, "Missing amount - specify how much you're paying", {}

        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you're making this payment", {}

        try:
            state = self.get_acp_state()
            
            # Check if job is cancelled
            if any(c["jobId"] == jobId for c in state["jobs"]["cancelled"]):
                return FunctionResultStatus.FAILED, "Cannot pay - this job has been cancelled", {}
            
            job = next(
                (c for c in state["jobs"]["active"]["as_a_buyer"] if c["job_id"] == job_id),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your buyer jobs - check the ID and verify you're the buyer", {}

            if job["phase"] != AcpJobPhasesDesc.NEGOTIATION:
                return FunctionResultStatus.FAILED, f"Cannot pay - job is in '{job['phase']}' phase, must be in 'negotiation' phase", {}


            self.acp_client.pay_for_job(
                job_id,
                job["memo"][0]["id"],
                amount,
                reasoning
            )

            if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None and tweet_content is not None:
                tweet_id = job.get("tweet_history", [])[0].get("tweet_id") if job.get("tweet_history") else None
                if tweet_id:
                    self._tweet_job(job_id, tweet_content, tweet_id)

            return FunctionResultStatus.DONE, json.dumps({
                "job_id": job_id,
                "amount_paid": amount,
                "timestamp": datetime.now().timestamp()
            }), {}
        except Exception as e:
            print(traceback.format_exc())
            return FunctionResultStatus.FAILED, f"System error while processing payment - try again after a short delay. {str(e)}", {}

    @property
    def deliver_job(self) -> Function:
        job_id_arg = Argument(
            name="job_id",
            type="integer",
            description="The job ID you are delivering for",
        )

        reasoning_arg = Argument(
            name="reasoning",
            type="string",
            description="Why you are making this delivery",
        )

        args = [job_id_arg, reasoning_arg]
        
        if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None:
            tweet_content_arg = Argument(
                name="tweet_content",
                type="string",
                description="Tweet content about your delivery for the specific job. MUST NOT TAG THE BUYER. This is to avoid spamming the buyer's feed with your delivery.",
            )
            args.append(tweet_content_arg)

        return Function(
            fn_name="deliver_job",
            fn_description="Completes a sale by delivering items to the buyer",
            args=args,
            executable=self._deliver_job_executable
        )

    def _deliver_job_executable(self, job_id: int, reasoning: str, tweet_content: Optional[str] = None) -> Tuple[FunctionResultStatus, str, dict]:
        if not job_id:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're delivering for", {}
            
        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you're making this delivery", {}

        try:
            state = self.get_acp_state()

            # Check if job is cancelled
            if any(c["jobId"] == jobId for c in state["jobs"]["cancelled"]):
                return FunctionResultStatus.FAILED, "Cannot deliver - this job has been cancelled", {}
            
            job = next(
                (c for c in state["jobs"]["active"]["as_a_seller"] if c["job_id"] == job_id),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your seller jobs - check the ID and verify you're the seller", {}

            if job["phase"] != AcpJobPhasesDesc.TRANSACTION:
                return FunctionResultStatus.FAILED, f"Cannot deliver - job is in '{job['phase']}' phase, must be in 'transaction' phase", {}

            produced = next(
                (i for i in self.produced_inventory if i.job_id == job["job_id"]),
                None
            )

            if not produced:
                return FunctionResultStatus.FAILED, "Cannot deliver - you should be producing the deliverable first before delivering it", {}

            deliverable = IDeliverable(
                type=produced.type,
                value=produced.value
            )

            self.acp_client.submit_job_deliverable(
                job_id,
                deliverable,
            )

            if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None and tweet_content is not None:
                tweet_id = job.get("tweet_history", [])[0].get("tweet_id") if job.get("tweet_history") else None
                if tweet_id:
                    self._tweet_job(job_id, tweet_content, tweet_id)
                
            return FunctionResultStatus.DONE, json.dumps({
                "status": "success",
                "job_id": job_id,
                "deliverable": deliverable.model_dump_json(),
                "timestamp": datetime.now().timestamp()
            }), {}
        except Exception as e:
            print(traceback.format_exc())
            return FunctionResultStatus.FAILED, f"System error while delivering items - try again after a short delay. {str(e)}", {}

    def _tweet_job(self, job_id: int, content: str, tweet_id: Optional[str] = None):
        if not hasattr(self, 'twitter_plugin') or self.twitter_plugin is None:
            return

        job = self.acp_client.get_job_by_onchain_id(job_id)
        if not job:
            raise Exception("ERROR (tweetJob): Job not found")

              
        if tweet_id :
            response = self.twitter_plugin.twitter_client.create_tweet(
                text=content,
                in_reply_to_tweet_id=tweet_id
            )
        else:
            response = self.twitter_plugin.twitter_client.create_tweet(text=content)


        role = "buyer" if job.client_address.lower() == self.acp_client.agent_address.lower() else "seller"

        # Safely extract tweet ID
        tweet_id = None
        if isinstance(response, dict):
            tweet_id = response.get('data', {}).get('id') or response.get('id')
        
        context = {
            **(job.context or {}),
            'tweets': [
                *((job.context or {}).get('tweets', [])),
                {
                    'type': role,
                    'tweetId': tweet_id,
                    'content': content,
                    'createdAt': int(datetime.now().timestamp() * 1000)
                },
            ],
        }

        response = requests.patch(
            f"{self.acp_base_url}/jobs/{job_id}/context",
            headers={
                "Content-Type": "application/json",
                "wallet-address": self.acp_client.agent_address,
            },
            json={"data": {"context": context}}
        )

        if not response.ok:
            raise Exception(f"ERROR (tweetJob): {response.status_code} {response.text}")
