from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field

class PaymentResponse(BaseModel):
    object: str = "payment"
    id: str = Field(..., description="Unique ID for the payment.")
    status: str = Field(..., description="Current status of the payment.")
    payment_amount: float = Field(..., gt=0, description="The amount for the payment, must be positive.")
    sending_agent_id: str = Field(..., description="Unique ID of the sending agent.")
    sending_agent_name: str = Field(..., description="Name of the sending agent.")
    receiving_agent_id: str = Field(..., description="Unique ID of the receiving agent.")
    receiving_agent_name: str = Field(..., description="Name of the receiving agent.")
    settlement_network: str = Field(..., description="network used for settlement.")
    currency: str = Field(..., description="Currency used in the crypto bridge (e.g., USDT, USDC, BTC, ETH).")
    transaction_fee: float = Field(..., ge=0, description="Transaction fee for the payment, must be non-negative.")
    conversation_id: str = Field(..., description="Identifier for the conversation linked to the payment.")
    transaction_hash: Optional[str] = Field(..., description="Transaction hash for the payment on the network")
    created_at: datetime = Field(..., description="The entity create timestamp")
    updated_at: datetime = Field(..., description="The entity update timestamp")

class AssetAccountBase(BaseModel):
    object: str = "account"
    id: str = Field(..., description="Unique identifier for the asset account.")
    balance: float = Field(0.0, ge=0, description="Current balance, must be non-negative.")
    asset: str = Field(..., max_length=50, description="Asset of the virtual currency.")
    created_at: datetime = Field(..., description="The entity create timestamp")
    updated_at: datetime = Field(..., description="The entity update timestamp")
    network: str = "Solana"

class AssetAccountRead(AssetAccountBase):
    wallet_address: str = Field(default=None, max_length=255, description="network address for agent wallet")

class AgentDataPlaneResponse(BaseModel):
    object: str = "agent_details"
    id: str = Field(description="Unique identifier for the agent")
    agent_type: str = Field()
    account: list[AssetAccountRead] = Field(..., description="Agent account balance information")

