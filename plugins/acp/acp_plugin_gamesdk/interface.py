from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Literal, Dict, Any, Callable
from pydantic import BaseModel, ConfigDict
from twitter_plugin_gamesdk.twitter_plugin import TwitterPlugin
from virtuals_acp import VirtualsACP, ACPContractConfig, DEFAULT_CONFIG

from virtuals_acp.models import ACPJobPhase, IDeliverable, ACPGraduationStatus, ACPOnlineStatus


class AcpPluginOptions(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str
    twitter_plugin: TwitterPlugin | None = None
    cluster: Optional[str] = None
    evaluator_cluster: Optional[str] = None
    graduation_status: Optional[ACPGraduationStatus] = None
    online_status: Optional[ACPOnlineStatus] = None
    job_expiry_duration_mins: Optional[int] = None
    keep_completed_jobs: Optional[int] = None
    keep_cancelled_jobs: Optional[int] = None
    keep_produced_inventory: Optional[int] = None


class AcpClientOptions(BaseModel):
    wallet_private_key: str
    agent_wallet_address: str
    entity_id: int
    config: ACPContractConfig = DEFAULT_CONFIG
    on_evaluate: Optional[Callable] = None
    on_new_task: Optional[Callable] = None


class AcpOffering(BaseModel):
    name: str
    price: float

    def __str__(self) -> str:
        return f"Offering(name={self.name}, price={self.price})"


class AcpJobPhasesDesc(str, Enum):
    REQUEST = "request"
    NEGOTIATION = "pending_payment"
    TRANSACTION = "in_progress"
    EVALUATION = "evaluation"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"


ACP_JOB_PHASE_MAP: Dict[ACPJobPhase, AcpJobPhasesDesc] = {
    ACPJobPhase.REQUEST: AcpJobPhasesDesc.REQUEST,
    ACPJobPhase.NEGOTIATION: AcpJobPhasesDesc.NEGOTIATION,
    ACPJobPhase.TRANSACTION: AcpJobPhasesDesc.TRANSACTION,
    ACPJobPhase.EVALUATION: AcpJobPhasesDesc.EVALUATION,
    ACPJobPhase.COMPLETED: AcpJobPhasesDesc.COMPLETED,
    ACPJobPhase.REJECTED: AcpJobPhasesDesc.REJECTED,
    ACPJobPhase.EXPIRED: AcpJobPhasesDesc.EXPIRED,
}


ACP_JOB_PHASE_REVERSE_MAP: Dict[str, ACPJobPhase] = {
    "request": ACPJobPhase.REQUEST,
    "pending_payment": ACPJobPhase.NEGOTIATION,
    "in_progress": ACPJobPhase.TRANSACTION,
    "evaluation": ACPJobPhase.EVALUATION,
    "completed": ACPJobPhase.COMPLETED,
    "rejected": ACPJobPhase.REJECTED,
    "expired": ACPJobPhase.EXPIRED,
}


class AcpRequestMemo(BaseModel):
    id: int

    def __repr__(self) -> str:
        return f"Memo(ID: {self.id})"


class ITweet(BaseModel):
    type: Literal["buyer", "seller"]
    tweet_id: str
    content: str
    created_at: int


class IAcpJob(BaseModel):
    job_id: Optional[int]
    client_name: Optional[str]
    provider_name: Optional[str]
    desc: str
    price: str
    provider_address: Optional[str]
    phase: AcpJobPhasesDesc
    memo: List[AcpRequestMemo]
    tweet_history: Optional[List[Optional[ITweet]]]

    def __repr__(self) -> str:
        return (
            f"Job ID: {self.job_id}, "
            f"Client Name: {self.client_name}, "
            f"Provider Name: {self.provider_name}, "
            f"Description: {self.desc}, "
            f"Price: {self.price}, "
            f"Provider Address: {self.provider_address}, "
            f"Phase: {self.phase.value}, "
            f"Memo: {self.memo}, "
            f"Tweet History: {self.tweet_history}"
        )


class IInventory(IDeliverable):
    job_id: int
    client_name: Optional[str]
    provider_name: Optional[str]


class AcpJobsSection(BaseModel):
    as_a_buyer: List[IAcpJob]
    as_a_seller: List[IAcpJob]

    def __str__(self) -> str:
        buyer_jobs = "\n".join([f"#{i+1} {str(job)}" for i, job in enumerate(self.as_a_buyer)])
        seller_jobs = "\n".join([f"#{i+1} {str(job)}" for i, job in enumerate(self.as_a_seller)])
        return f"As Buyer:\n{buyer_jobs}\n\nAs Seller:\n{seller_jobs}"


class AcpJobs(BaseModel):
    active: AcpJobsSection
    completed: List[IAcpJob]
    cancelled: List[IAcpJob]

    def __str__(self) -> str:
        return (
            f"💻 Jobs\n"
            f"🌕 Active Jobs:\n{self.active}\n"
            f"🟢 Completed:\n{self.completed}\n"
            f"🔴 Cancelled:\n{self.cancelled}"
        )


class AcpInventory(BaseModel):
    acquired: List[IInventory]
    produced: Optional[List[IInventory]]

    def __str__(self) -> str:
        return (
            f"💼 Inventory\n"
            f"Acquired: {self.acquired}\n"
            f"Produced: {self.produced}"
        )


class AcpState(BaseModel):
    inventory: AcpInventory
    jobs: AcpJobs

    def __str__(self) -> str:
        return (
            f"🤖 Agent State".center(50, '=') + "\n"
            f"{str(self.inventory)}\n"
            f"{str(self.jobs)}\n"
            f"State End".center(50, '=')
        )

