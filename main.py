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
from fastapi import FastAPI, HTTPException
from middlewares.input_validation import InputValidationMiddleware
from routers.graph_router import router as graph_router


from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_pool()
    init_pinecone()
    yield
    close_pool()

app = FastAPI(lifespan=lifespan)

class TaskRouterInput(BaseModel):
    input: str
    user_id: str = "user-123"

app.add_middleware(InputValidationMiddleware)

# user query endpoint
app.include_router(graph_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}