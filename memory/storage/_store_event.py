from memory.clients.pinecone_conn import get_index
from utils.embed import embed_text
from datetime import datetime, timedelta, timezone
import uuid
import re
import dateutil.parser as dparser
import dateparser
from datetime import datetime
from datetime import datetime
import pytz

def now_ist():
    IST = pytz.timezone("Asia/Kolkata")
    return datetime.now(IST)

EVENT_TTL = 60 * 60 * 24 * 15  # 15 days

def normalize_time(text):
    now = now_ist()
    return dateparser.parse(
        text,
        settings={
            "RELATIVE_BASE": now,
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": True
        }
    )

def _store_event(content: str, user_id: str , time: str):
    """
    Extract event datetime + embed + upsert to Pinecone.
    """

    # --- 1) Extract datetime from text ---
    event_dt = normalize_time(time)

    active = True if event_dt and event_dt > datetime.now(timezone.utc) else False

    # --- 2) Embed text ---
    try:
        index = get_index()
        vector = embed_text(content)
    except Exception as e:
        print(f"❌ Embedding/Index error: {e}")
        return

    event_id = str(uuid.uuid4())

    # --- 3) Metadata ---
    metadata = {
        "type": "events",
        "text": content,
        "active": active,
        "created_at": now_ist().isoformat(),
        "event_time": event_dt.isoformat() if event_dt else ""
    }

    # --- 4) Upsert ---
    try:
        index.upsert(
            vectors=[{
                "id": event_id,
                "values": vector,
                "metadata": metadata
            }],
            namespace=user_id,
            ttl=EVENT_TTL
        )
        print(f"🟢 Event stored → {content}")
    except Exception as e:
        print(f"❌ Upsert failed: {e}")