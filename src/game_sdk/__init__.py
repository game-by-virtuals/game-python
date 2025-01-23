"""
GAME SDK - A Python SDK for building autonomous agents.

This package provides tools and utilities for creating, managing, and running
autonomous agents that can perform various tasks through function execution.

Example:
    Basic usage:

    >>> from game_sdk import Agent, Worker, Function
    >>> agent = Agent(api_key="your_key", name="MyAgent", ...)
    >>> worker = Worker(api_key="your_key", description="My Worker", ...)
"""

from game_sdk.version import (
    __version__,
    __author__,
    __author_email__,
    __description__,
    __url__,
)

from game_sdk.game.agent import Agent, WorkerConfig
from game_sdk.game.worker import Worker
from game_sdk.game.custom_types import (
    Function,
    Argument,
    FunctionResult,
    FunctionResultStatus,
    ActionType,
    ActionResponse,
)

# Define what symbols to expose when using 'from game_sdk import *'
__all__ = [
    # Classes
    'Agent',
    'Worker',
    'WorkerConfig',
    'Function',
    'Argument',
    'FunctionResult',
    'FunctionResultStatus',
    'ActionType',
    'ActionResponse',
    # Version info
    '__version__',
    '__author__',
    '__author_email__',
    '__description__',
    '__url__',
]