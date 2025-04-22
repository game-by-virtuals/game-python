from collections.abc import Callable
import signal
import sys
from typing import List, Dict, Any, Optional,Tuple
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import traceback
import time

import socketio
import socketio.client

from game_sdk.game.agent import WorkerConfig
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
from twitter_plugin_gamesdk.game_twitter_plugin import GameTwitterPlugin
from acp_plugin_gamesdk.acp_client import AcpClient
from acp_plugin_gamesdk.acp_token import AcpToken
from acp_plugin_gamesdk.interface import AcpJobPhasesDesc, IDeliverable, IInventory, AcpJob

@dataclass
class AcpPluginOptions:
    api_key: str
    acp_token_client: AcpToken
    twitter_plugin: TwitterPlugin | GameTwitterPlugin = None
    cluster: Optional[str] = None
    evaluator_cluster: Optional[str] = None
    on_evaluate: Optional[Callable[[IDeliverable], Tuple[bool, str]]] = None
    on_phase_change: Optional[Callable[[AcpJob], None]] = None
    

SocketEvents = {
    "JOIN_EVALUATOR_ROOM": "joinEvaluatorRoom",
    "LEAVE_EVALUATOR_ROOM": "leaveEvaluatorRoom", 
    "ON_EVALUATE": "onEvaluate",
    "ROOM_JOINED" : "roomJoined",
    "ON_PHASE_CHANGE": "onPhaseChange"
}

class AcpPlugin:
    def __init__(self, options: AcpPluginOptions):
        print("Initializing AcpPlugin")
        self.acp_token_client = options.acp_token_client
        self.acp_client = AcpClient(options.api_key, options.acp_token_client, options.acp_token_client.acp_base_url)
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
        self.twitter_plugin = None
        if (options.twitter_plugin is not None):
            self.twitter_plugin = options.twitter_plugin
            
        self.produced_inventory: List[IInventory] = []
        self.acp_base_url = self.acp_token_client.acp_base_url if self.acp_token_client.acp_base_url is None else "https://acpx-staging.virtuals.io/api"
        if options.on_evaluate is not None or options.on_phase_change is not None:
            print("Initializing socket")
            self.socket = None
            if options.on_evaluate is not None:
                self.on_evaluate = options.on_evaluate
            if options.on_phase_change is not None:
                self.on_phase_change = options.on_phase_change
            self.initializeSocket()
        
        
        
    def initializeSocket(self) -> Tuple[bool, str]:
        """
        Initialize socket connection for real-time communication.
        Returns a tuple of (success, message).
        """
        try:
            self.socket = socketio.Client()
                
            # Set up authentication before connecting
            self.socket.auth = {
                "evaluatorAddress": self.acp_token_client.agent_wallet_address
            }
            
            # Connect socket to GAME SDK dev server
            self.socket.connect("https://sdk-dev.game.virtuals.io", auth=self.socket.auth)
            
            if (self.socket.connected):
                self.socket.emit(SocketEvents["JOIN_EVALUATOR_ROOM"], self.acp_token_client.agent_wallet_address)
        
            
            # Set up event handler for evaluation requests
            @self.socket.on(SocketEvents["ON_EVALUATE"])
            def on_evaluate(data):
                if self.on_evaluate:
                    deliverable = data.get("deliverable")
                    memo_id = data.get("memoId")
                    
                    is_approved, reasoning = self.on_evaluate(deliverable)
                    
                    self.acp_token_client.sign_memo(memo_id, is_approved, reasoning)
                    
                        # Set up event handler for phase changes
            @self.socket.on(SocketEvents["ON_PHASE_CHANGE"])
            def on_phase_change(data):
                if hasattr(self, 'on_phase_change') and self.on_phase_change:
                    print(f"on_phase_change: {data}")
                    self.on_phase_change(data)
            
            # Set up cleanup function for graceful shutdown
            def cleanup():
                if self.socket:
                    print("Disconnecting socket")
                    import time
                    time.sleep(1)
                    self.socket.disconnect()
                    
                    
            
            def signal_handler(sig, frame):
                cleanup()
                sys.exit(0)
                
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            return True, "Socket initialized successfully"
            
        except Exception as e:
            return False, f"Failed to initialize socket: {str(e)}"
    
    
    def set_on_phase_change(self, on_phase_change: Callable[[AcpJob], None]) -> None:
        self.on_phase_change = on_phase_change

    def add_produce_item(self, item: IInventory) -> None:
        self.produced_inventory.append(item)
        
    def reset_state(self) -> None:
        self.acp_client.reset_state()
        
    def delete_completed_job(self, job_id: int) -> None:
        self.acp_client.delete_completed_job(job_id)
        
    def get_acp_state(self) -> Dict:
        server_state = self.acp_client.get_state()
        server_state.inventory.produced = self.produced_inventory
        state = asdict(server_state)
        return state

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
            * asABuyer: Pending resource purchases
            * asASeller: Pending design requests
          - jobs.completed: Successfully fulfilled projects
          - jobs.cancelled: Terminated or rejected requests
          - Each job tracks:
            * phase: request (seller should response to accept/reject to the job) → pending_payment (as a buyer to make the payment for the service) → in_progress (seller to deliver the service) → evaluation → completed/rejected
        """
        
    def _search_agents_executable(self,reasoning: str, keyword: str) -> Tuple[FunctionResultStatus, str, dict]:
        if not reasoning:
            return FunctionResultStatus.FAILED, "Reasoning for the search must be provided. This helps track your decision-making process for future reference.", {}
            
        agents = self.acp_client.browse_agents(self.cluster, keyword)
        
        if not agents:
            return FunctionResultStatus.FAILED, "No other trading agents found in the system. Please try again later when more agents are available.", {}
        
        return FunctionResultStatus.DONE, json.dumps({
            "availableAgents": [{"id": agent.id, "name": agent.name, "description": agent.description, "wallet_address": agent.wallet_address, "offerings": [{"name": offering.name, "price": offering.price} for offering in agent.offerings] if agent.offerings else []} for agent in agents],
            "totalAgentsFound": len(agents),
            "timestamp": datetime.now().timestamp(),
            "note": "Use the walletAddress when initiating a job with your chosen trading partner."
        }), {}

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
            name="sellerWalletAddress",
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
            name="serviceRequirements",
            type="string",
            description="Detailed specifications for service-based items",
        )
        
        require_evaluation_arg = Argument(
            name="requireEvaluation",
            type="boolean",
            description="Decide if your job request is complex enough to spend money for evaluator agent to assess the relevancy of the output. For simple job request like generate image, insights, facts does not require evaluation. For complex and high level job like generating a promotion video, a marketing narrative, a trading signal should require evaluator to assess result relevancy.",
        )
        
        evaluator_keyword_arg = Argument(
            name="evaluatorKeyword",
            type="string",
            description="Keyword to search for a evaluator",
        )

        args = [seller_wallet_address_arg, price_arg, reasoning_arg, service_requirements_arg, require_evaluation_arg, evaluator_keyword_arg]
        
        if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None:
            tweet_content_arg = Argument(
                name="tweetContent",
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

    def _initiate_job_executable(self, sellerWalletAddress: str, price: str, reasoning: str, serviceRequirements: str, requireEvaluation: bool, evaluatorKeyword: str, tweetContent: Optional[str] = None) -> Tuple[FunctionResultStatus, str, dict]:
        if not price:
            return FunctionResultStatus.FAILED, "Missing price - specify how much you're offering per unit", {}
        
        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you're making this purchase request", {}
        
        try:
            state = self.get_acp_state()

            if state["jobs"]["active"]["asABuyer"]:
                return FunctionResultStatus.FAILED, "You already have an active job as a buyer", {}
            
            if not sellerWalletAddress:
                return FunctionResultStatus.FAILED, "Missing seller wallet address - specify the agent you want to buy from", {}
            
            if bool(requireEvaluation) and not evaluatorKeyword:
                return FunctionResultStatus.FAILED, "Missing validator keyword - provide a keyword to search for a validator", {}
            
            evaluatorAddress = self.acp_token_client.get_agent_wallet_address()
            
            if bool(requireEvaluation):
                validators = self.acp_client.browse_agents(self.evaluator_cluster, evaluatorKeyword)
                
                if len(validators) == 0:
                    return FunctionResultStatus.FAILED, "No evaluator found - try a different keyword", {}
                
                evaluatorAddress = validators[0].wallet_address
            
            # ... Rest of validation logic ...
            job_id = self.acp_client.create_job(
                sellerWalletAddress,
                float(price),
                serviceRequirements,
                evaluatorAddress
            )
            
            if (hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None and tweetContent is not None):
                post_tweet_fn = self.twitter_plugin.get_function('post_tweet')
                tweet_id = post_tweet_fn(tweetContent, None).get('data', {}).get('id')
                if (tweet_id is not None):
                    self.acp_client.add_tweet(job_id, tweet_id, tweetContent)
                    print("Tweet has been posted")

            return FunctionResultStatus.DONE, json.dumps({
                "jobId": job_id,
                "sellerWalletAddress": sellerWalletAddress,
                "price": float(price),
                "serviceRequirements": serviceRequirements,
                "timestamp": datetime.now().timestamp(),
            }), {}
        except Exception as e:
            print(traceback.format_exc())
            return FunctionResultStatus.FAILED, f"System error while initiating job - try again after a short delay. {str(e)}", {}

    @property
    def respond_job(self) -> Function:
        job_id_arg = Argument(
            name="jobId",
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
                name="tweetContent",
                type="string",
                description="Tweet content that will be posted about this job. Must include the seller's Twitter handle (with @ symbol) to notify them",
            )
            args.append(tweet_content_arg)

        return Function(
            fn_name="respond_to_job",
            fn_description="Accepts or rejects an incoming 'request' job",
            args=args,
            executable=self._respond_job_executable
        )

    def _respond_job_executable(self, jobId: int, decision: str, reasoning: str, tweetContent: Optional[str] = None) -> Tuple[FunctionResultStatus, str, dict]:
        if not jobId:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're responding to", {}
        
        if not decision or decision not in ["ACCEPT", "REJECT"]:
            return FunctionResultStatus.FAILED, "Invalid decision - must be either 'ACCEPT' or 'REJECT'", {}
            
        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you made this decision", {}

        try:
            state = self.get_acp_state()
            
            job = next(
                (c for c in state["jobs"]["active"]["asASeller"] if c["jobId"] == jobId),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your seller jobs - check the ID and verify you're the seller", {}

            if job["phase"] != AcpJobPhasesDesc.REQUEST:
                return FunctionResultStatus.FAILED, f"Cannot respond - job is in '{job['phase']}' phase, must be in 'request' phase", {}

            self.acp_client.response_job(
                jobId,
                decision == "ACCEPT",
                job["memo"][0]["id"],
                reasoning
            )
            
            if (hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None and tweetContent is not None):
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
        job_id_arg = Argument(
            name="jobId",
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
                name="tweetContent",
                type="string",
                description="Tweet content that will be posted about this job. Must include the seller's Twitter handle (with @ symbol) to notify them",
            )
            args.append(tweet_content_arg)

        return Function(
            fn_name="pay_job",
            fn_description="Processes payment for an accepted purchase request",
            args=args,
            executable=self._pay_job_executable
        )

    def _pay_job_executable(self, jobId: int, amount: float, reasoning: str, tweetContent: Optional[str] = None) -> Tuple[FunctionResultStatus, str, dict]:
        if not jobId:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're paying for", {}

        if not amount:
            return FunctionResultStatus.FAILED, "Missing amount - specify how much you're paying", {}

        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you're making this payment", {}

        try:
            state = self.get_acp_state()
            
            job = next(
                (c for c in state["jobs"]["active"]["asABuyer"] if c["jobId"] == jobId),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your buyer jobs - check the ID and verify you're the buyer", {}

            if job["phase"] != AcpJobPhasesDesc.NEGOTIATION:
                return FunctionResultStatus.FAILED, f"Cannot pay - job is in '{job['phase']}' phase, must be in 'negotiation' phase", {}


            self.acp_client.make_payment(
                jobId,
                amount,
                job["memo"][0]["id"],
                reasoning
            )
            
            if (hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None and tweetContent is not None):
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
            print(traceback.format_exc())
            return FunctionResultStatus.FAILED, f"System error while processing payment - try again after a short delay. {str(e)}", {}

    @property
    def deliver_job(self) -> Function:
        job_id_arg = Argument(
            name="jobId",
            type="integer",
            description="The job ID you are delivering for",
        )

        deliverable_type_arg = Argument(
            name="deliverableType",
            type="string",
            description="Type of the deliverable",
        )

        deliverable_arg = Argument(
            name="deliverable",
            type="string",
            description="The deliverable item",
        )

        reasoning_arg = Argument(
            name="reasoning",
            type="string",
            description="Why you are making this delivery",
        )

        args = [job_id_arg, deliverable_type_arg, deliverable_arg, reasoning_arg]
        
        if hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None:
            tweet_content_arg = Argument(
                name="tweetContent",
                type="string",
                description="Tweet content that will be posted about this job. Must include the seller's Twitter handle (with @ symbol) to notify them",
            )
            args.append(tweet_content_arg)

        return Function(
            fn_name="deliver_job",
            fn_description="Completes a sale by delivering items to the buyer",
            args=args,
            executable=self._deliver_job_executable
        )

    def _deliver_job_executable(self, jobId: int, deliverableType: str, deliverable: str, reasoning: str, tweetContent: Optional[str] = None) -> Tuple[FunctionResultStatus, str, dict]:
        if not jobId:
            return FunctionResultStatus.FAILED, "Missing job ID - specify which job you're delivering for", {}
            
        if not reasoning:
            return FunctionResultStatus.FAILED, "Missing reasoning - explain why you're making this delivery", {}
            
        if not deliverable:
            return FunctionResultStatus.FAILED, "Missing deliverable - specify what you're delivering", {}

        try:
            state = self.get_acp_state()
            
            job = next(
                (c for c in state["jobs"]["active"]["asASeller"] if c["jobId"] == jobId),
                None
            )

            if not job:
                return FunctionResultStatus.FAILED, "Job not found in your seller jobs - check the ID and verify you're the seller", {}

            if job["phase"] != AcpJobPhasesDesc.TRANSACTION:
                return FunctionResultStatus.FAILED, f"Cannot deliver - job is in '{job['phase']}' phase, must be in 'transaction' phase", {}

            produced = next(
                (i for i in self.produced_inventory if i.jobId == job["jobId"]),
                None
            )

            if not produced:
                return FunctionResultStatus.FAILED, "Cannot deliver - you should be producing the deliverable first before delivering it", {}

            deliverable: dict = {
                "type": deliverableType,
                "value": deliverable
            }

            self.acp_client.deliver_job(
                jobId,
                json.dumps(deliverable),
            )
            
            if (hasattr(self, 'twitter_plugin') and self.twitter_plugin is not None and tweetContent is not None):

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
            print(traceback.format_exc())
            return FunctionResultStatus.FAILED, f"System error while delivering items - try again after a short delay. {str(e)}", {}

    @property
    def wait(self) -> Function:

        wait_duration_arg = Argument(
            name="waitDuration",
            type="integer",
            description="The duration to wait in seconds (minimum 30 seconds)",
        )
        
        return Function(
            fn_name="wait",
            fn_description="Waits for a specified amount of time",
            args=[wait_duration_arg],
            executable=self._wait_executable
        )
    
    def _wait_executable(self, waitDuration: int) -> Tuple[FunctionResultStatus, str, dict]:
        if waitDuration < 30:
            waitDuration = 30
        time.sleep(waitDuration)
        return FunctionResultStatus.DONE, f"Waited for {waitDuration} seconds", {}