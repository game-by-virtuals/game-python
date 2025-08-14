from enum import Enum
from typing import Any


def to_serializable_dict(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: to_serializable_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_serializable_dict(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        return {
            k: to_serializable_dict(v)
            for k, v in vars(obj).items()
            if not k.startswith("_")
        }
    else:
        return obj
