import re
from typing import Dict, Any, List
from langsmith import traceable


IDENTITY_PATTERNS = {
    "name": r"\b(my name is|call me|my name)\b(?:\s+([A-Za-z ]+))?" ,
    "birthday": r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
    "age": r"\b(\d{1,2})\s*(years old|yo)\b",
    "gender": r"\b(male|female|non-binary|trans|man|woman)\b",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "phone_number": r"\b\d{10}\b",
    "country": r"\b(india|usa|canada|france|germany|uk|china|japan)\b",
    "city": r"\b(delhi|mumbai|bangalore|pune|hyderabad|chennai|city)\b",
    "upi_id": r"[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}",
    "address": r"\b(street|road|nagar|sector|colony|apt|building|address)\b",
    "timezone": r"GMT[+-]\d+",
    "language": r"\b(english|hindi|spanish|french|german|tamil|telugu)\b",
}

def classify_identity(text: str):
    text_lower = text.lower()
    for field, pattern in IDENTITY_PATTERNS.items():
        if re.search(pattern, text_lower):
            return field
    print(text)
    return None


def classify_item(text: str) -> Dict[str, Any]:

    t = text.lower()

    # --- Identity ---
    identity_field = classify_identity(text)
    if identity_field:
        return {
            "type": "identity",
            "sub_type": identity_field,
            "text": text
        }

    # --- Habits ---
    if any(word in t for word in ["every day", "daily", "usually", "typically", "i always", "i often"]):
        return {
            "type": "habits",
            "text": text
        }

    # --- Preferences ---
    if any(word in t for word in ["i like", "i love", "i prefer", "my favourite", "my favorite" , "preferences"]):
        return {
            "type": "preferences",
            "text": text
        }

    # --- Events ---
    if any(word in t for word in ["today", "yesterday", "tomorrow", "tonight", "this week", "last week" , "event" , "events"]):
        return {
            "type": "events",
            "text": text
        }

    # --- Task ---
    if any(word in t for word in ["remind me", "set a reminder", "todo", "task", "deadline"]):
        return {
            "type": "task",
            "text": text
        }

    # --- Default fallback ---
    return {
        "type": "unknown",
        "text": text
    }

@traceable
def classification_node2(state: Dict[str, Any]):

    def process_list(items: List[Dict[str, Any]]):
        result = []
        for item in items:
            text = item.get("text", "")
            classified = classify_item(text)
            result.append(classified)
        return result

    return {
        "memories_to_write": process_list(state.get("memories_to_write", [])),
        "questions": process_list(state.get("questions", [])),
        "ignore_queue": process_list(state.get("ignore", [])),
    }