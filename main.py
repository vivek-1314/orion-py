import json
from fastapi import FastAPI, Body
import time
from contextlib import asynccontextmanager
from pydantic import BaseModel
from graph.taskRouterGraph import graph  # your LangGraph graph
from utils.embed import embed_text
# from utils.pinecone_db import vector_db
from memory.clients.supabase_conn import init_db_pool, close_pool
from memory.clients.pinecone_conn import init_pinecone

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_pool()
    init_pinecone()
    yield
    close_pool()

app = FastAPI(lifespan=lifespan)

class TaskRouterInput(BaseModel):
    input: str
    messages: list = []
    result: dict = {}
    user_id: str = "user-123"

def pretty_state(state: dict):
    print("===============Current State:===============")
    filtered = {k: v for k, v in state.items() if k != "messages"}
    print(json.dumps(filtered, indent=4, ensure_ascii=False))

@app.post("/run-graph")
async def run_graph(payload: TaskRouterInput):
    """
    Runs the LangGraph task router graph with input state.
    """
    initial_state = {
        "input": payload.input,
        "user_input_for_memory": payload.input,
        "messages": payload.messages,
        "result": payload.result,
        "user_id": payload.user_id
    }

    print("Initial state:", initial_state)

    answer_state = await graph.ainvoke(initial_state)

    pretty_state(answer_state)

    return {
        "status": "success",
        "final_state": answer_state
    }

class MemoryInput(BaseModel):
    user_id: str
    content: str
    memory_type: str

@app.post("/add-memory")
async def add_memory(data: MemoryInput):
    vector = embed_text(data.content)
    vector = vector.tolist() if hasattr(vector, "tolist") else list(vector)

    memory_id = f"mem-{int(time.time() * 1000)}"

    vector_db.upsert(
        namespace=data.user_id,
        vector_id=memory_id,
        vector_values=vector,
        metadata={
            "content": data.content,
            "type": data.memory_type,
            "timestamp": time.time()
        }
    )

    return {
        "status": "saved",
        "memory_id": memory_id,
        "content": data.content
    }