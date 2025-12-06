from langgraph.graph import StateGraph , START , END
from states.taskRouterState import TaskRouterState 
from nodes.intentClassifier import intentClassifier
from nodes.memoryRetriver import memoryRetriever
from nodes.final_answer import final_answer_node
from nodes.memory_to_write import memory_extractor
from langgraph.prebuilt import ToolNode 
import asyncio

builder = StateGraph(TaskRouterState) 

# cnt = 1
# def route_tools(state: TaskRouterState):
#     """Route to 'tools' if last message has tool calls; else END."""
#     global cnt
#     if cnt > 4 :
#         return END
    
#     cnt = cnt+1 
#     messages = state.get("messages", [])
#     if not messages:
#         print("⚠️ No messages found — ending.")
#         return "END"

#     ai_message = messages[-1]

#     # Some models include empty tool_calls — we handle that safely
#     if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:   
#         print("🧩 Tool calls found → routing to tools node.")
#         return "tools"

#     print("✅ No tool calls → ending graph.")
#     return "END"

# builder.add_node("task_manager" , task_manager) 
# def memoryRetriever_sync(state):
#     return asyncio.run(memoryRetriever(state))

builder.add_node("intent_classifier" , intentClassifier)
builder.add_node("memoryRetriever", memoryRetriever , async_node=True)
builder.add_node("final_answer_node" , final_answer_node)
builder.add_node("memory_to_write" , memory_extractor) 

builder.add_edge(START , "intent_classifier")
builder.add_edge("intent_classifier" , "memoryRetriever" )
builder.add_edge("memoryRetriever" , "final_answer_node")

# builder.add_edge("memoryAssigner" , END)
builder.add_edge(START , "memory_to_write") 
builder.add_edge("memory_to_write" , "final_answer_node")

builder.add_edge("final_answer_node" , END)


# builder.add_edge("memoryAssigner" , "memoryRetriver") 
# builder.add_edge("memoryRetriver" , "final_answer_node")
# builder.add_edge("final_answer_node" , END)

graph =  builder.compile()

# from PIL import Image as PILImage
# from IPython.display import Image, display
# image_data = graph.get_graph().draw_mermaid_png()
# with open("trip_graph.png", "wb") as f:
#     f.write(image_data)
# img = PILImage.open("trip_graph.png")
# img.show()