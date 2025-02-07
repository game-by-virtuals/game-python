from typing import Dict, Any, Optional
from pydantic import BaseModel

class RouterRequest(BaseModel):
    query: str

class RouteInfo(BaseModel):
    tool: str
    confidence: float
    parameters: Optional[Dict[str, Any]] = None
    description: str

class RouterResponse(BaseModel):
    original_query: str
    route: RouteInfo
    response: Dict[str, Any]
