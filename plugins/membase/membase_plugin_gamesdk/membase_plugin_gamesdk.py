import os
from typing import Literal, Optional
from membase.memory.multi_memory import MultiMemory
from membase.memory.message import Message

class MembasePlugin:
    def __init__(self, account: Optional[str] = None, agent_name: Optional[str] = None, auto_upload_to_hub: bool = False, preload_from_hub: bool = False):
        if not account:
            self.account = os.getenv("MEMBASE_ACCOUNT")
        else:
            self.account = account
        if not self.account:
            raise ValueError("MEMBASE_ACCOUNT is not set and provided account is None")
        
        if not agent_name:
            self.id = os.getenv("MEMBASE_ID")
        else:
            self.id = agent_name
        if not self.id:
            self.id = self.account

        self._multi_memory = MultiMemory(
            membase_account=self.account,
            auto_upload_to_hub=auto_upload_to_hub,
            preload_from_hub=preload_from_hub,
        )

    # memory_type: user,system,assistant | default: user
    def add_memory(self, memory: str, memory_type: Literal["user", "system", "assistant"] = "user", conversation_id: Optional[str] = None):
        msg = Message(
            name=self.id,
            content=memory,
            role=memory_type,
        )
        self._multi_memory.add(msg, conversation_id)

    def get_memory(self, conversation_id: Optional[str] = None, recent_n: Optional[int] = None):
        return self._multi_memory.get(conversation_id, recent_n)
    
    def switch_conversation_id(self, conversation_id: Optional[str] = None):
        self._multi_memory.update_conversation_id(conversation_id)
    
    def reload_memory(self, conversation_id: str):
        self._multi_memory.load_from_hub(conversation_id)