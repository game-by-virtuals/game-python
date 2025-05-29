from dataclasses import dataclass
from enum import IntEnum, Enum
from typing import List, Literal, Optional, Callable

@dataclass
class AcpOffering:
    name: str
    price: float

    def __str__(self) -> str:
        output = (
            f"Offering(name={self.name}, price={self.price})"
        )
        return output
    
@dataclass
class AcpAgent:
    id: str
    name: str
    twitter_handle: str
    description: str
    wallet_address: str
    offerings: Optional[List[AcpOffering]]
    score: Optional[float]
    explanation: Optional[str]

    def __str__(self) -> str:
        offer = ""
        if self.offerings:
            for index, off in enumerate(self.offerings):
                offer += f"{index+1}. {str(off)}\n"

        output = (
            f"😎 Agent ID={self.id}\n"
            f"Name={self.name}, Description={self.description}, Wallet={self.wallet_address}\n"
            f"Offerings:\n{offer}"
            f"Score:\n{self.score}"
            f"Explanation:\n{self.explanation}"
        )
        return output
    
class AcpJobPhases(IntEnum):
    REQUEST = 0
    NEGOTIATION = 1
    TRANSACTION = 2
    EVALUATION = 3
    COMPLETED = 4
    REJECTED = 5

class AcpJobPhasesDesc(str, Enum):
    REQUEST = "request"
    NEGOTIATION = "pending_payment"
    TRANSACTION = "in_progress"
    EVALUATION = "evaluation"
    COMPLETED = "completed"
    REJECTED = "rejected"

@dataclass
class AcpRequestMemo:
    id: int
    createdAt: int

    def __repr__(self) -> str:
        output = f"Memo(ID: {self.id}, created at: {self.createdAt})"
        return output
    
@dataclass
class ITweet:
    type: Literal["buyer", "seller"]
    tweet_id: str
    content: str
    created_at: int

@dataclass
class AcpJob:
    jobId: Optional[int]
    clientName : Optional[str]
    providerName: Optional[str]
    desc: str
    price: str
    providerAddress: Optional[str]
    clientAddress: Optional[str]
    phase: AcpJobPhasesDesc
    memo: List[AcpRequestMemo]
    tweetHistory : ITweet | List
    lastUpdated: int
    getAgentByWalletAddress: Optional[Callable[[str], AcpAgent]]
    

    def __repr__(self) -> str:
        output =(
            f"Job ID: {self.jobId}, "
            f"Client Name: {self.clientName}, "
            f"Provider Name: {self.providerName}, "
            f"Description: {self.desc}, "
            f"Price: {self.price}, "
            f"Provider Address: {self.providerAddress}, "
            f"Client Address: {self.clientAddress}, "
            f"Phase: {self.phase.value}, "
            f"Memo: {self.memo}, "
            f"Tweet History: {self.tweetHistory}, "
            f"Last Updated: {self.lastUpdated})"
        ) 
        return output

@dataclass
class IDeliverable:
    type: str
    value: str
    clientName: Optional[str]
    providerName: Optional[str]
@dataclass
class IInventory(IDeliverable):
    jobId: int
    clientName: Optional[str]
    providerName: Optional[str]

@dataclass
class AcpJobsSection:
    asABuyer: List[AcpJob]
    asASeller: List[AcpJob]

    def __str__(self) -> str:
        buyer_jobs = ""
        for index, job in enumerate(self.asABuyer):
            buyer_jobs += f"#{index+1} {str(job)} \n"

        seller_jobs = ""
        for index, job in enumerate(self.asASeller):
            seller_jobs += f"#{index+1} {str(job)} \n"

        output = (
            f"As Buyer:\n{buyer_jobs}\n"
            f"As Seller:\n{seller_jobs}\n"
        )
        return output

@dataclass
class AcpJobs:
    active: AcpJobsSection
    completed: List[AcpJob]
    cancelled: List[AcpJob]

    def __str__(self) -> str:
        output = (
            f"💻 Jobs\n"
            f"🌕 Active Jobs:\n{self.active}\n"
            f"🟢 Completed:\n{self.completed}\n"
            f"🔴 Cancelled:\n{self.cancelled}\n"
        )
        return output
    
@dataclass
class AcpInventory:
    acquired: List[IInventory]
    produced: Optional[List[IInventory]]

    def __str__(self) -> str:
        output = (
            f"💼 Inventory\n"
            f"Acquired: {self.acquired}\n"
            f"Produced: {self.produced}\n"
        )
        return output

@dataclass
class AcpState:
    inventory: AcpInventory
    jobs: AcpJobs

    def __str__(self) -> str:
        output = (
            f"🤖 Agent State".center(50, '=') + "\n" + \
            f"{str(self.inventory)}\n" + \
            f"{str(self.jobs)}\n" + \
            f"State End".center(50, '=') + "\n"
        )
        return output