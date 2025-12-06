import json
from states.taskRouterState import TaskRouterState
from llm import llm

def final_answer_node(state: TaskRouterState):
    """
    Final Answer Node: generates a natural human-like paragraph
    from state.tasks and their fetched memories using the LLM.
    """
    tasks = state.get("tasks", [])
    memory_stored = state.get("memory_stored", {})
    if not tasks:
        state["final_answer"] = "I don't have any information to answer that."
        return state

    # Build LLM messages
    messages = [
        ("user",
         f"""You are Orion’s Final Answer Agent.
            Your role:
            - Read the system state, which contains:
                • A list of extracted tasks.
                • For each task: the relevant memories already fetched.
                • A list of newly stored memories (memory_stored).

            How to behave:
            1. Generate a natural, human-like, coherent paragraph that answers the user's tasks.
            2. Use ONLY the memories marked as relevant for each task. Ignore all other memories entirely.
            3. Keep the response short, clear, natural, and TTS-friendly.
            4. If memory_stored is NOT empty:
                - Inform the user, in a simple human-friendly way, about the new info that has been saved for the future.
                - Do NOT say where it was saved or how.
            5. If memory_stored is empty:
                - Do NOT mention anything about saving memory.
            6. If any task is unclear or missing information:
                - Politely ask the user for clarification.
            7. Never mention the system, tasks, memory fetches, or internal mechanisms. Output should feel like a normal chat response.

            Inputs provided to you:
            {tasks}
            {json.dumps(memory_stored, indent=4)}

            Your output:
            - A single human-like paragraph answering the tasks using only their relevant memories.
            - Optionally, a short friendly line stating which new details were remembered (only if memory_stored is non-empty).
            """ )]

    # Invoke the LLM
    response = llm.invoke(messages)

    # state["final_answer"] = response.content
    return {"final_answer": response.content}