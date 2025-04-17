from dataclasses import dataclass
from enum import IntEnum, Enum
from typing import List, Dict, Literal, Optional

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
    description: str
    wallet_address: str
    offerings: Optional[List[AcpOffering]]

    def __str__(self) -> str:
        offer = ""
        if self.offerings:
            for index, off in enumerate(self.offerings):
                offer += f"{index+1}. {str(off)}\n"

        output = (
            f"😎 Agent ID={self.id}\n"
            f"Name={self.name}, Description={self.description}, Wallet={self.wallet_address}\n"
            f"Offerings:\n{offer}"
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
class AcpJob:
    jobId: int
    desc: str
    price: str
    phase: AcpJobPhasesDesc
    memo: List[AcpRequestMemo]
    lastUpdated: int

    def __repr__(self) -> str:
        output =(
            f"Job ID: {self.jobId}, "
            f"Description: {self.desc}, "
            f"Price: {self.price}, "
            f"Phase: {self.phase.value}, "
            f"Memo: {self.memo}, "
            f"Last Updated: {self.lastUpdated})"
        ) 
        return output

@dataclass
class IDeliverable:
    type: Literal["url", "text"]
    value: str

@dataclass
class IInventory(IDeliverable):
    job_id: int

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
    aquired: List[IInventory]
    produced: Optional[List[IInventory]]

    def __str__(self) -> str:
        output = (
            f"💼 Inventory\n"
            f"Acquired: {self.aquired}\n"
            f"Produced: {self.produced}\n"
        )
        return output

@dataclass
class AcpState:
    inventory: AcpInventory
    jobs: AcpJobs

    def __str__(self) -> str:
        output = (
            f"========= 🤖 Agent State =========\n"
            f"{str(self.inventory)}\n"
            f"{str(self.jobs)}\n"
            f"========= State End ==============\n"
        )
        return output