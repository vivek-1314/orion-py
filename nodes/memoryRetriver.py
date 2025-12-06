# memory_fetcher.py

from memory.clients.pinecone_conn import get_index
from utils.embed import embed_text
from datetime import datetime, timezone
from psycopg2.extras import RealDictCursor
import psycopg2
from memory.clients.supabase_conn import fetch_identity_memory


async def memoryRetriever(state):
    """
    Fetches memory depending on task metadata.
    The task MUST contain:
    - memory_needed (bool)
    - memory_type (string or null)
    - input (task-specific user input)
    """

    tasks = state["tasks"]
    user_id = state["user_id"]  # assumed saved in state

    updated_tasks = []

    for task in tasks:
        # default memory
        memory = None

        if( task.get("memory_needed") ):
            memory_type = task.get("memory_type")
            task_input = task.get("input")
            what_exact_memory = task.get("what_exact_memory")

            # embed the task input
            vector = embed_text(what_exact_memory)

            if memory_type == "identity":
                # fetch from Postgres
                memory = fetch_identity_memory(user_id , what_exact_memory)

            elif memory_type in ["preferences", "habits", "events", "emotions", "tasks"]:
                # fetch from Pinecone
                memory = fetch_pinecone_memory(memory_type, vector, user_id)

        # attach memory into the task object
        task_with_memory = {
            **task,          # copy everything from original
            "memory": memory # append memory result
        }

        updated_tasks.append(task_with_memory)

    # save back to state
    # state["tasks"] = updated_tasks
    return {"tasks": updated_tasks}

# ---------------------------------------------------
# 1. FETCH IDENTITY MEMORY FROM POSTGRES
# ---------------------------------------------------

# def fetch_identity_memory(user_id):
#     """
#     Fetch identity facts from Postgres.
#     """
#     try:
#         conn = psycopg2.connect(
#             host="localhost",
#             database="orion",
#             user="postgres",
#             password="password"
#         )
#         cur = conn.cursor(cursor_factory=RealDictCursor)

#         cur.execute("SELECT * FROM identity WHERE user_id = %s", (user_id,))
#         result = cur.fetchone()

#         cur.close()
#         conn.close()

#         return result

#     except Exception as e:
#         print("IDENTITY FETCH ERROR:", e)
#         return None

# ---------------------------------------------------
# 2. FETCH OTHER MEMORY FROM PINECONE
# ---------------------------------------------------

def fetch_pinecone_memory(memory_type, vector, user_id):
    """
    memory_type: preference | habit | event | emotion | task
    vector: embedding list
    """
    # print("Fetching", memory_type, "memory for user:", user_id)
    try:
        index = get_index()
        print("Pinecone index obtained:", memory_type)

        result = index.query(
            vector=vector,
            top_k=10,
            include_metadata=True,
            namespace= user_id,  # Specify the user's namespace here
            filter={"type": memory_type}  # Optional filter inside that namespace
        )

        print("Raw Pinecone fetch result:", result)

        # return clean list of memories
        memories = [
            {
                "id": match["id"],
                "score": match["score"],
                "metadata": match["metadata"]
            }
            for match in result.matches
        ]
        # print("Clean Pinecone fetch result:", memories)
        return memories

    except Exception as e:
        print("PINECONE FETCH ERROR:", e)
        return []
