import json
from llm import llm
from langsmith import traceable

@traceable
def segmentation_node1(state):

    """
    Segments user query into memory_to_write, memory_to_fetch, ignore_queue using an LLM .

    state: dict containing at least 'input'
    """

    query = state.get("input", "").strip()

    # Prompt for the LLM
    prompt = f"""
        You are a memory segmentation and classification assistant.

        1. Segment the user query into individual facts (name, birthdate, city, etc.).
        2. For each segment, classify into one of three categories:
            a. memory_to_write → user is providing info to remember
            b. memory_to_fetch → user is asking for stored info
            c. ignore → chit-chat or irrelevant
        3. Also detect if any segment implicitly requires memory fetch.

        Return **ONLY valid JSON**  in this format:
        {{
            "memory_to_write": [
                {{"text": <text>}}
            ],
            "memory_to_fetch": [
                {{"text": <text>}}
            ],
            "ignore_queue": [
                {{"text": <text>}}
            ]
        }}

        User query: "{query}"
        """

    # Get response from your LLM instance
    response_text = llm.invoke(prompt)  
    response = response_text.content

    # Parse JSON safely
    try:
        result = extract_json(response)
        print("✅ segmentation layer - status : success")
    except Exception as e:
        # Fallback: put everything in ignore_queue
        result = {
            "memory_to_write": [],
            "memory_to_fetch": [],
            "ignore_queue": [{"text": query}]
        }
        print("❌ segmentation layer - status : error")

    return {
        "memories_to_write": result.get('memory_to_write'),
        "questions": result.get('memory_to_fetch', []),
        "ignore": result.get('ignore_queue', [])
    }


# json extractor
def extract_json(text):
    # If it's an AIMessage, get the content
    if hasattr(text, "content"):
        text = text.content

    text = text.strip()

    # Strip code fences like ```json ... ```
    if text.startswith("```"):
        parts = text.split("```")
        # parts = ["", "json\n{...}", ""]
        if len(parts) >= 2:
            text = parts[1]  # remove first ```
        text = text.strip()
        # Remove optional "json" tag
        if text.startswith("json"):
            text = text[4:].strip()

    return json.loads(text)