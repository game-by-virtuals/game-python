from dataclasses import dataclass
from enum import IntEnum, Enum
from typing import List, Dict, Literal, Optional

@dataclass
class AcpOffering:
    name: str
    price: float

@dataclass
class AcpAgent:
    id: str
    name: str
    description: str
    wallet_address: str
    offerings: Optional[List[AcpOffering]]

class AcpClusters(str, Enum):
    HEDGEFUND = "hedgefund"
    MEDIAHOUSE = "mediahouse"

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
    created_at: int

@dataclass
class AcpJob:
    job_id: int
    desc: str
    price: str
    phase: AcpJobPhasesDesc
    memo: List[AcpRequestMemo]
    last_updated: int

@dataclass
class IDeliverable:
    type: Literal["url", "text"]
    value: str

@dataclass
class IInventory(IDeliverable):
    job_id: int

@dataclass
class AcpJobsSection:
    as_a_buyer: List[AcpJob]
    as_a_seller: List[AcpJob]

@dataclass
class AcpJobs:
    active: AcpJobsSection
    completed: List[AcpJob]
    cancelled: List[AcpJob]

@dataclass
class AcpInventory:
    aquired: List[IInventory]
    produced: List[IInventory]

@dataclass
class AcpState:
    inventory: AcpInventory
    jobs: AcpJobs
