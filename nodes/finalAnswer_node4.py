from llm import llm   # your LLM wrapper
from langsmith import traceable

# ============================================================
# FINAL ANSWER NODE 4    [working for generating final answer using user input + fetched memories] (using llm)
# ============================================================

@traceable
async def final_answer_node(state):
    """
    Build the final answer using:
    - user input
    - fetched memories (from memory_reader)
    """

    user_input = state.get("input", "")
    memories = state.get("retrieved_memories", [])

    # Convert memories to structured text
    memory_text = ""
    if memories:
        lines = []
        for m in memories:
            lines.append(f"- ({m['type']}) {m['text']}")
        memory_text = "\n".join(lines)

    prompt = f"""
        You are Orion, a proactive AI companion.
        Generate a helpful, context-aware answer.

        USER SAID:
        {user_input}

        RELEVANT USER MEMORIES:
        {memory_text if memory_text else "No relevant memories found."}

        INSTRUCTION:
        GREETING_WORDS = ["hi", "hello", "hey", "hii", "hy", "hello orion"]
            if user_input in **only** GREETING_WORDS:
            return f"Hi Vivek! How can I help you?"
        Use the relevant memories naturally only if they improve understanding.
        Your answer must be friendly, concise, and helpful. refer user as vivek
        """

    # Call LLM
    response = await llm.ainvoke(prompt)
    answer = response.content

    # Store final result in state
    state["final_answer"] = answer

    return state
