from utils.pinecone_conn import get_index
from utils.supabase_conn import get_conn
from utils.embed import embed_text
from psycopg2 import sql
from langsmith import traceable

@traceable
async def memory_reader(input, user_id):
    """
    1) Takes [{type, text}]
    2) Searches Pinecone within user's namespace
    3) Fetches matched memory text from Supabase memory_pool
    4) Returns all matched memories
    """

    index = get_index()
    conn = get_conn()
    cur = conn.cursor()

    results = []

    # for every item in questions array 
    for item in input:

        mem_type = item.get("type")
        query_text = item.get("text")

        if not mem_type or not query_text:
            continue
        
        # fetching identity  memory 
        if mem_type == "identity" :
            sub_type = item.get("sub_type") 
            if not sub_type : ValueError("no subtype given for identity memory")
            
            query = sql.SQL("""
                SELECT {column}
                FROM "userMemory"
                WHERE id = %s
                """).format(
                column=sql.Identifier(sub_type)
            )
            cur.execute(query, (user_id,))
            row = cur.fetchone()
            if not row : continue 
    
            matched_text = row[0]

            # ---- Step 4: Add to result ----
            results.append({
                "type": mem_type,
                "sub_type" : sub_type,
                "text": matched_text
            })

            continue 
        
        # pre checks
        if mem_type not in ["preferences" , "events" , "habits"] :
            ValueError("envalid mem_type to fetch info") 
            continue 

        # fetching habits prefrences and events memory

        # ---- Step 1: embed incoming text ----
        embedding = embed_text(query_text)

        # ---- Step 2: Search Pinecone ----
        query_response = index.query(
            vector=embedding,
            top_k=1,
            include_values=False,
            include_metadata=True,
            namespace=user_id,
            filter={"user_id": user_id, "type": mem_type}
        )

        if not query_response.matches:
            continue
        
        matched_id = query_response.matches[0].id

        # ---- Step 3: Fetch text from Supabase memory_pool ----
        cur.execute(
            """
            SELECT text FROM memories_pool
            WHERE id = %s AND m_type = %s;
            """,
            (matched_id, mem_type)
        )
        row = cur.fetchone()

        if not row:
            continue
        
        matched_text = row[0]

        # ---- Step 4: Add to result ----
        results.append({
            "id": matched_id,
            "type": mem_type,
            "text": matched_text
        })

    conn.close()

    print("📤 memory_reader fetched:", results)

    return {"retrieved_memories": results}
