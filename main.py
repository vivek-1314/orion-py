import json
from fastapi import FastAPI, Body
import time
from contextlib import asynccontextmanager
from pydantic import BaseModel
from graph.taskRouterGraph import graph 
from utils.embed import embed_text
from utils.supabase_conn import init_db_pool, close_pool
from utils.pinecone_conn import init_pinecone
from langsmith import traceable

from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print()
    init_db_pool()
    init_pinecone()
    yield
    close_pool()

app = FastAPI(lifespan=lifespan)

class TaskRouterInput(BaseModel):
    input: str
    user_id: str = "user-123"

# exposed point for running the graph
@app.post("/run-graph")
async def run_graph(payload: TaskRouterInput):
    """
    Runs the LangGraph task router graph with input state.
    """

    initial_state = {
        "input": payload.input,
        "user_id": payload.user_id,
    }

    print("Initial state:", initial_state)

    answer_state = await graph.ainvoke(initial_state)

    print("final__state" , answer_state )

    return {
        "status": "success",
        "final_state": answer_state
    }
