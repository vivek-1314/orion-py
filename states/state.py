from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph.message import add_messages
from typing import Annotated
from langgraph.graph import StateGraph 


class state(TypedDict, total=False):
    input: str
    user_id: str
    memories_to_write: List[Dict[str, Any]]
    questions: List[Dict[str, Any]]
    ignore: List[Dict[str, Any]]
    retrieved_memories: List[Dict[str, Any]]
    final_answer: str | None