import re
from typing import Dict, Any, List
from langsmith import traceable
from datetime import datetime, timedelta
import dateparser
import re
import pytz
from dateutil.relativedelta import relativedelta

tz = pytz.timezone("Asia/Kolkata")

# helper identity field patterns
IDENTITY_PATTERNS = {
    "name": r"\b(my name is|call me|my name)\b(?:\s+([A-Za-z ]+))?" ,
    "birthday": r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
    "age": r"\b(\d{1,2})\s*(years old|yo)\b",
    "gender": r"\b(male|female|non-binary|trans|man|woman)\b",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "phone_number": r"\b\d{10}\b",
    "country": r"\b(india|usa|canada|france|germany|uk|china|japan)\b",
    "city": r"\b(delhi|mumbai|bangalore|pune|hyderabad|chennai|city|bhopal)\b",
    "upi_id": r"[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}",
    "address": r"\b(street|road|nagar|sector|colony|apt|building|address)\b",
    "timezone": r"GMT[+-]\d+",
    "language": r"\b(english|hindi|spanish|french|german|tamil|telugu)\b",
}

# helper func to classify identity fields
def classify_identity(text: str):
    text_lower = text.lower()
    for field, pattern in IDENTITY_PATTERNS.items():
        if re.search(pattern, text_lower):
            return field
    return None

# func to classify a single item
def classify_item(text: str, _time: str) -> Dict[str, Any]:

    t = text.lower()

    # --- Identity ---
    identity_field = classify_identity(text)
    if identity_field:
        now = datetime.now(tz)
        ttl = now + relativedelta(months=5)
        return {
            "type": "identity",
            "sub_type": identity_field,
            "text": text,
            "ttl": ttl
        }

    # --- Habits ---
    if any(word in t for word in ["every day", "daily", "usually", "typically", "i always", "i often"]):
        now = datetime.now(tz)
        ttl = now + relativedelta(months=8)
        return {
            "type": "habits",
            "text": text,
            "ttl": ttl
        }

    # --- Preferences ---
    if any(word in t for word in ["i like", "i love", "i prefer", "my favourite", "my favorite" , "preferences"]):
        now = datetime.now(tz)
        ttl = now + relativedelta(months=5)
        return {
            "type": "preferences",
            "text": text,
            "ttl": ttl
        }

    # --- Events ---
    if any(word in t for word in ["today", "yesterday", "tomorrow", "tonight", "this week", "last week" , "event" , "events"]):
        now = datetime.now(tz)
        event_time, ttl = resolve_event_ttl(_time,now)
        print(ttl)
        return {
            "type": "events",
            "text": text,
            "event_time": event_time,
            "ttl": ttl,
        }

    # --- Task ---
    if any(word in t for word in ["remind me", "set a reminder", "todo", "task", "deadline"]):
        now = datetime.now(tz)
        ttl = now + relativedelta(days=5)
        return {
            "type": "task",
            "text": text,
            "ttl": ttl
        }

    # --- Default fallback ---
    return {
        "type": "unknown",
        "text": text
    }


# ---------------------------------------------------------------------------
# CLASSIFICATION NODE 2    [working for classifying segmented items into types/subtypes]
# ---------------------------------------------------------------------------
@traceable
def classification_node2(state: Dict[str, Any]):

    def process_list(items: List[Dict[str, Any]]):
        result = []
        for item in items:
            text = item.get("text", "")
            _time = item.get("_time", "")
            classified = classify_item(text, _time)
            result.append(classified)
        return result

    return {
        "memories_to_write": process_list(state.get("memories_to_write", [])),
        "questions": process_list(state.get("questions", [])),
        "ignore_queue": process_list(state.get("ignore", [])),
    }


# ------------- date parse for ttl and event time ----------------
MAX_EVENT_HORIZON_DAYS = 60      # 2 months
EVENT_BUFFER_DAYS = 5            # normal buffer
FALLBACK_TTL_DAYS = 2            # fallback buffer

def extract_date_phrase(text: str):
    text = text.lower()
    pattern = r"""
    \b(
        today|tomorrow|tonight|yesterday |
        
        after\s+\d+\s+(day|days|week|weeks|month|months) |
        
        (on|at|around|by)?\s*
        \d{1,2}(st|nd|rd|th)?\s*(of)?\s*
        (jan|january|feb|february|mar|march|apr|april|
         may|jun|june|jul|july|aug|august|
         sep|september|oct|october|nov|november|
         dec|december) |
        
        (on|at|around|by)?\s*
        \d{1,2}/\d{1,2}/\d{2,4} |
        
        tomorrow\s+(at)?\s+\d{1,2}(:\d{2})?\s*(am|pm)?
    )\b
    """
    match = re.search(pattern, text, re.IGNORECASE | re.VERBOSE)
    return match.group(0) if match else None

def resolve_event_ttl(text: str, now: datetime, timezone="Asia/Kolkata"):
    now = datetime.now(tz)
    FB_ttl = now + timedelta(days=FALLBACK_TTL_DAYS)

    # CASE 1: No date phrase found → fallback logic
    if not text:
        return None, FB_ttl

    parsed_time = dateparser.parse(
        text,
        settings={
            "RELATIVE_BASE": now,
            "PREFER_DATES_FROM": "future",
            "TIMEZONE": timezone,
            "RETURN_AS_TIMEZONE_AWARE": True
        }
    )

    # CASE 2: Date phrase exists but still not parsed → fallback
    if not parsed_time:
        return None, FB_ttl

    # CASE 3: Parsed successfully
    # If only date present → assume end of day
    if parsed_time.hour == 0 and parsed_time.minute == 0:
        event_time = parsed_time.replace(hour=23, minute=59)
    else:
        event_time = parsed_time

    # DROP: too far in future (> 2 months)
    if event_time - now > timedelta(days=MAX_EVENT_HORIZON_DAYS):
        return None, FB_ttl

    # ✅ Normal TTL
    ttl = event_time + timedelta(days=EVENT_BUFFER_DAYS)
    print(event_time, ttl)
    return event_time, ttl