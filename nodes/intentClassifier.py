from states.taskRouterState import TaskRouterState
from llm import llm
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage 
import json

def strip_code_fences(text: str) -> str:
    text = text.strip()
    # remove ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        # remove leading ```json and ending ```
        text = text.strip("`")
        # also remove optional "json" prefix
        text = text.replace("json", "", 1).strip()
    return text


def intentClassifier(state: TaskRouterState):

    user_input = state["input"]  # renamed to avoid conflict with Python keyword

    # Fixed PromptTemplate: use 'template', not 'prompt', and escape all JSON braces
    prompt = PromptTemplate(
        input_variables=["input"],
        template="""
Analyze the following user input. The input may contain multiple tasks.
Return a JSON array of tasks, where each task has:
- "input": the text relevant to that task only
- "intent": the goal/action the user wants to perform (e.g., set_reminder, schedule_meeting, order_item)
- "entities": a dictionary of relevant entities for that task
- "memory_needed": true or false only fetch memory if it is needed for the task , not for general chat or tasks which are adding info to memory
- "memory_type": one of: ["identity", "preferences", "habits", "events", "emotions", "tasks"], null
- "what_exact_memory": description if needed.

Rules:
1. If the input contains multiple actions, split them into separate tasks.
2. For casual conversation, greetings, jokes, or small talk, set intent as "general_chat" and entities as empty.
3. Ensure that "intent" captures the **user's goal**, not just keywords.
4. Extract as many relevant entities as possible (like time, date, contact, location, item, quantity, etc.).
5. Respond ONLY in JSON format exactly like this.

Example:
User Input: "remind me to call Mom at 6 PM. and also, what's my favorite music?"
Response:
{{
    "tasks": [
        {{
            "input": "call my mom at 6 PM",
            "intent": "set_reminder",
            "entities": {{
                "action": "call",
                "contact": "mom",
                "time": "6 PM"
            }}
            "memory_needed": false,
            "memory_type": null,
            "what_exact_memory": null
        }},
        {{
            "input": "what's my favorite music",
            "intent": "retrieve_preference",
            "entities": {{
                "preference_type": "music"
            }},
            "memory_needed": true,
            "memory_type": "preference",
            "what_exact_memory": "favorite music" : **Only return the key requested. no fuzzy words like "user's name ...etc"**
        }}
    ]
}}

Now analyze the user input:
User Input: "{input}"
"""
    )

    # format the prompt
    final_prompt = prompt.format(input=user_input)

    # add user message to conversation
    state["messages"].append(HumanMessage(content=final_prompt))

    # get LLM response
    response = llm.invoke(state["messages"])

    # append LLM response to messages
    state["messages"].append(response)

    # parse JSON safely
    print("LLM Response Content:", response.content)  # Debugging line
    try:
        cleaned = strip_code_fences(response.content)
        extracted = json.loads(cleaned)  
    except Exception:
        extracted = {"tasks": []}
    state["tasks"] = extracted.get("tasks")

    print("Extracted tasks:", json.dumps(state["tasks"], indent=2))
    return {"tasks": extracted.get("tasks")}