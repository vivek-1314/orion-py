import asyncio
import uuid
from datetime import datetime, timedelta
from utils.pinecone_conn import get_index
from utils.supabase_conn import get_conn
from utils.embed import embed_text
from datetime import datetime
from langsmith import traceable


# ============================================================
# MAIN WRITER NODE 3a    [working for writing memories to Pinecone + Postgres]
# ============================================================

@traceable
async def memory_writer(memories_to_write, user_id):
    """
    Handles ALL memories in parallel.
    Each memory is processed by process_single_memory()
    """
    tasks = []

    for memory in memories_to_write:
        tasks.append(asyncio.create_task(
            process_single_memory(memory, user_id)
        ))

    if tasks:
        await asyncio.gather(*tasks)

    print("✅ memory added or updated" , len(memories_to_write)) 
    return {"written": len(memories_to_write)}


# ============================================================
# PROCESS A SINGLE MEMORY (parallel per memory)
# ============================================================

async def process_single_memory(memory, user_id):
    """
    Process a single memory:
    1. Generate embedding
    2. Upsert to Pinecone
    3. Insert JSONB into Postgres
    All steps run in parallel when possible.
    """

    mem_type = memory.get("type")
    text = memory.get("text")
    if mem_type in ["unknown", "identity"]:
        return
    
    # Compute embedding
    embedding = embed_text(text)
    # print("embedding done")

    # Memory ID for Pinecone
    pinecone_id = str(uuid.uuid4())

    # TTL logic
    if memory.get("ttl"):
        ttl = memory.get("ttl")
    else:
        ttl = None
    
    print(ttl) 

    
    if memory.get("event_time"):
        event_time = memory.get("event_time")
    else:
        event_time = None

    # Prepare Pinecone metadata
    metadata = {
        # "id": pinecone_id,
        "type": mem_type,
        "user_id": user_id,
        "ttl": ttl.isoformat() if ttl else None
    }

    index = get_index()
    conn = get_conn()

    is_new, existing_id = await check_memory_is_new(index, embedding, user_id, mem_type) 
    # print(is_new , existing_id)

    # Run Pinecone + Postgres in parallel
    await asyncio.gather(
        upsert_to_pinecone(index, pinecone_id, embedding, metadata, user_id, is_new, existing_id),
        add_memory_to_supabase(
            conn, user_id, pinecone_id, mem_type, text, is_new, existing_id, embedding, event_time, ttl=ttl
        )
    )

    conn.close()

# ============================================================
# PINECONE UPSERT
# ============================================================

async def upsert_to_pinecone(index, pinecone_id, embedding, metadata, user_namespace, is_new, existing_id):
    if is_new:
        # Insert new vector
        index.upsert(
            vectors=[(pinecone_id, embedding, metadata)],
            namespace=user_namespace
        )
        return f"Inserted new memory {pinecone_id}"
    else:
        # Update metadata for existing vector
        if existing_id is None:
            raise ValueError("existing_id must be provided when updating an existing memory")
        
        index.upsert(
            vectors=[
                {
                    "id": existing_id,
                    "values": embedding,
                    "metadata": metadata
                }
            ],
            namespace=user_namespace
        )
        return f"Updated existing memory {existing_id}"
    
# ============================================================
# POSTGRES APPEND
# ============================================================

async def add_memory_to_supabase(conn, user_id, pinecone_id, mem_type, text, is_new, existing_id,embedding, event_time, ttl):
    """
    Add or update memory:
    - If is_new, insert into memories_pool and append reference to userMemory
    - If not new, update the existing memory in memories_pool
    - Always ensure userMemory row exists and append pinecone_id to UUID array if new
    """
    # print("inside" , mem_type) 
    if mem_type not in ["preferences", "habits", "events"]:
        raise ValueError(f"Invalid memory type: {mem_type}")

    cur = conn.cursor()

    # Step 1: Insert or update memories_pool
    if is_new:
        # print("inside new") 
        # Insert new memory
        pool_query = """
        INSERT INTO memories_pool (id, user_id, m_type, text, ttl, event_time, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (id) DO NOTHING;
        """
        cur.execute(
            pool_query,
            (pinecone_id, user_id, mem_type, text, ttl, event_time)
        )
    else:
        # Update existing memory
        update_pool_query = """
        UPDATE memories_pool
        SET text = %s,
            ttl = %s,
            event_time = %s,
            updated_at = NOW()
        WHERE id = %s;
        """
        cur.execute(
            update_pool_query,
            (text, ttl, event_time, existing_id)
        )

    # Step 2: Ensure userMemory row exists
    cur.execute(
        """
        INSERT INTO "userMemory" (id, preferences, habits, events, created_at)
        VALUES (%s, ARRAY[]::uuid[], ARRAY[]::uuid[], ARRAY[]::uuid[], NOW())
        ON CONFLICT (id) DO NOTHING;
        """,
        (user_id,)
    )

    # Step 3: Append pinecone_id to the correct UUID array only if new
    if is_new:
        update_query = f"""
        UPDATE "userMemory"
        SET {mem_type} = 
            CASE
                WHEN {mem_type} IS NULL THEN ARRAY[%s::uuid]
                ELSE {mem_type} || ARRAY[%s::uuid]
            END,
            updated_at = NOW()
        WHERE id = %s;
        """
        cur.execute(
            update_query,
            (pinecone_id, pinecone_id, user_id)
        )

    conn.commit()

# ============================================================
# check memory is new or not [so we can decide insert vs update]
# ============================================================

async def check_memory_is_new(index, embedding, user_id, mem_type, similarity_threshold=0.85):  

    # Query the most similar vector for this user and memory type
    query_response = index.query(
        vector=embedding,
        top_k=1,
        include_values=False,
        include_metadata=True,
        namespace=user_id,      # <<< REQUIRED
        filter={"user_id": user_id, "type": mem_type}
    )

    if query_response.matches:
        match = query_response.matches[0]
        score = match.score  # similarity score (usually cosine)
        # print(score)
        existing_id = match.id
        if score >= similarity_threshold:
            # Memory is considered the same
            print("✅ updated memory")
            return False, existing_id

    # Memory is new
    return True, None
