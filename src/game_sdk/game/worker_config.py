"""
Worker configuration module for the GAME SDK.

This module defines the configuration classes used to set up workers.
"""

from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from game_sdk.game.custom_types import Function


class WorkerConfig(BaseModel):
    """
    Configuration for a worker in the GAME SDK.

    Attributes:
        id: Unique identifier for the worker
        worker_name: Name of the worker
        worker_description: Description of what the worker does
        functions: List of functions the worker can execute
        state: Optional initial state for the worker
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    worker_name: str
    worker_description: str
    functions: List[Function]
    state: Optional[Dict] = None
