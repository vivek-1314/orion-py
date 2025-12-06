from memory.clients.pinecone_conn import get_index
from utils.embed import embed_text
from datetime import datetime, timezone
import uuid

# TTLs in seconds
PREFERENCE_TTL = 60 * 60 * 24 * 365  # 1 year
HABIT_TTL = 60 * 60 * 24 * 180       # 6 months
MAX_ITEMS = 50  # max per type
SIMILARITY_THRESHOLD = 0.8  # cosine similarity threshold to merge

def _store_persistent(m_type: str, content: str, user_id: str):
    """
    Store persistent memory (preferences or habits) in Pinecone under namespace = user_id.
    Deduplicate semantically: if a similar memory exists, merge instead of inserting.
    Enforce max items per type (50), remove oldest if exceeding.
    TTL differs based on memory type.
    """
    try:
        vector = embed_text(content)
        if not vector:
            raise ValueError("Embedding returned empty vector!")

        index = get_index()
        ttl = PREFERENCE_TTL if m_type == "preferences" else HABIT_TTL

        # Step 1: Check for existing similar memory
        existing = index.query(
            vector=vector,
            top_k=1,
            include_metadata=True,
            namespace=user_id,
            filter={"type": {"$eq": m_type}}
        )

        if existing.matches:
            similarity = existing.matches[0].score
            if similarity > SIMILARITY_THRESHOLD:
                # Merge with existing memory
                existing_id = existing.matches[0].id
                merged_text = content
                metadata = existing.matches[0].metadata
                metadata["text"] = merged_text
                metadata["timestamp"] = datetime.now(timezone.utc)

                index.upsert(
                    vectors=[{
                        "id": existing_id,
                        "values": vector,
                        "metadata": metadata
                    }],
                    namespace=user_id,
                    ttl=ttl
                )
                print(f"🔄 Updated existing {m_type} → {merged_text}")
                return

        # Step 2: Insert as new memory
        item_id = str(uuid.uuid4())
        metadata = {
            "type": m_type,
            "text": content,
            "timestamp": datetime.now(timezone.utc)
        }
        index.upsert(
            vectors=[{
                "id": item_id,
                "values": vector,
                "metadata": metadata
            }],
            namespace=user_id,
            ttl=ttl
        )
        print(f"🟢 Stored new {m_type} → {content} (NS={user_id}, TTL={ttl}s)")

        # Step 3: Enforce MAX_ITEMS limit
        # Query top MAX_ITEMS + extra (to detect overflow)
        DUMMY_VECTOR = [0.0] * len(vector)
        current = index.query(
            vector=DUMMY_VECTOR,
            top_k=MAX_ITEMS + 10,
            include_metadata=True,
            namespace=user_id,
            filter={"type": {"$eq": m_type}}
        )

        if len(current.matches) > MAX_ITEMS:
            sorted_matches = sorted(current.matches, key=lambda m: m.metadata.get("timestamp"))
            to_delete = [m.id for m in sorted_matches[:-MAX_ITEMS]]  # keep newest MAX_ITEMS
            index.delete(ids=to_delete, namespace=user_id)
            print(f"⚠️ Removed {len(to_delete)} oldest {m_type} to maintain max {MAX_ITEMS}")

    except Exception as e:
        print(f"❌ Failed to store {m_type}: {e}")