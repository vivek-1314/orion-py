from datetime import timedelta
from .storage._store_identity import _store_identity
from .storage._store_persistent import _store_persistent
from .storage._store_event import _store_event  
from .storage._store_emotion import _store_emotion

class MemoryManager:
    def __init__(self, default_event_ttl_days=30, default_emotion_ttl_hours=6):
        print("Initializing MemoryManager")
        self.event_ttl = timedelta(days=default_event_ttl_days)
        self.emotion_ttl = timedelta(hours=default_emotion_ttl_hours)

    def store_memory(self, memory: dict , user_id: str):
        m_type = memory.get("memory_type")
        content = memory.get("content")

        if not content:
            return

        if m_type == "identity":
            _store_identity(content)
        elif m_type in ["preferences", "habits"]:
            _store_persistent(m_type, content , user_id=user_id)
        elif m_type == "events":
            _store_event(content, user_id=user_id, time=memory.get("time"))
        elif m_type == "emotions":
            _store_emotion(content)
        else:
            print(f"Unknown memory type: {m_type}")

    # Optional: batch storage
    def store_memories(self, memories: list , user_id: str):
        for mem in memories:
            self.store_memory(mem , user_id=user_id)