from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
import json
from llm import llm
from memory.memory_manager import MemoryManager 

def strip_code_fences(text: str) -> str:
    text = text.strip()
    # remove ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        # remove leading ```json and ending ```
        text = text.strip("`")
        # also remove optional "json" prefix
        text = text.replace("json", "", 1).strip()
    return text

def memory_extractor(state):

    user_input = state["user_input_for_memory"]

    prompt = PromptTemplate.from_template(
        template="""
You are a 'Memory Extraction Agent' for an AI assistant.
Your job: decide what parts of the user's message should be stored as **long-term memory**.

### Memory Rules:
Store a memory ONLY IF it belongs to one of these categories of the user:
1. Identity facts (name, age, birth_date, occupation, country or other personal facts only of user) **must include** key if is in
    (name, age, birth_date, occupation, country) in context example: content = "key: <value>"
2. Preferences (likes/dislikes in food, music, habits, routines)
3. Habits (repeated behaviors or routines)
4. For scheduled events (meetings, trips, deadlines), also extract the event time if present. Return it as: time: <extracted_time> , <desc>: <description> (e.g., content: today 3PM , <desc>: meeting with Bob)
5. Emotional states (clear expressions of emotion)
6. Tasks or goals mentioned by the user

NEVER store:
- temporary physical descriptions (“my charger is on the table”)
- random chit-chat
- non-personal info
- jokes, greetings, small talk

### Output Format:
Return ONLY JSON:

{
  "memories_to_write": [
    {
      "memory_type": **"<identity|preferences|habits|events|emotions|tasks>"**,
      "content": "example text"
    }
  ]
}

**only for event memory_type**, if time is extracted, include it in content as:
{
  "memories_to_write": [
    {
      "memory_type": **"<identity|preferences|habits|events|emotions|tasks>"**,
      "content": "desc",
      "time": "extracted_time",
    }
  ]
}**

If nothing should be stored, return:
{ "memories_to_write": [] }

Now analyze this user input:
"{{ input }}"
""",
        template_format="jinja2"
    )

    final_prompt = prompt.format(input=user_input)

    state["messages"].append(HumanMessage(content=final_prompt))
    response = llm.invoke(state["messages"])
    state["messages"].append(response)

    print("Memory Extractor Output (raw):", response.content)

    try:
        cleaned = strip_code_fences(response.content)
        extracted = json.loads(cleaned)  
    except Exception:
        extracted = {"memories_to_write": []}

    # state["memories_to_write"] = extracted.get("memories_to_write", [])

    # --- Use MemoryManager to store memories ---
    mem_manager = MemoryManager()
    mem_manager.store_memories(extracted.get("memories_to_write", []) , user_id="user-123")

    return {"memories_to_write" : extracted.get("memories_to_write", [])}