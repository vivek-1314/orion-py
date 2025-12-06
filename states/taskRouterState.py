from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph.message import add_messages
from langgraph.channels import LastValue
import operator
from typing import Annotated

class TaskRouterState(TypedDict, total=False):
    input: Annotated[str, operator.add]  
    user_input_for_memory: Annotated[str, operator.add]  
    user_id: Annotated[str, operator.add]  
    messages: Annotated[List, add_messages]
    tasks: List[Dict]
    memories_to_write: List[Dict[str, Any]]
    final_answer: str | None


