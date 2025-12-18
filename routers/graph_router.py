from pydantic import BaseModel
from fastapi import APIRouter, Request
from graph.taskRouterGraph import graph

router = APIRouter()

class TaskRouterInput(BaseModel):
    input: str
    user_id: str = "user-123"

# user query endpoint
@router.post("/run-graph")
async def run_graph(request: Request, payload: TaskRouterInput):
    initial_state = {
        "input": request.state.user_input,  # sanitized by middleware
        "user_id": request.state.user_id,
    }

    answer_state = await graph.ainvoke(initial_state)

    return {
        "status": "success",
        "final_state": answer_state
    }
