from langgraph.graph import StateGraph , START , END
from langgraph.prebuilt import ToolNode 
from states.state import state
from nodes.segmentation_node1 import segmentation_node1
from nodes.classification_node2 import classification_node2 
from nodes.memoryReader_node3b import memory_reader
from nodes.memoryWriter_node3a import memory_writer
import asyncio
from nodes.finalAnswer_node4 import final_answer_node

builder = StateGraph(state)

# router logic
async def router_node(state):
    tasks = []

    if state.get("memories_to_write"):
        tasks.append(asyncio.create_task(
            memory_writer(state["memories_to_write"], state["user_id"])
        ))

    if state.get("questions"):
        tasks.append(asyncio.create_task(
            memory_reader(state["questions"], state["user_id"])
        ))

    if not tasks:
            return state

    # === Process each result as soon as it finishes ===
    for future in asyncio.as_completed(tasks):
        res = await future

        if not res:
            continue

        # Merge the returned result into state
        for key, val in res.items():

            # append list values
            if key in state and isinstance(state[key], list) and isinstance(val, list):
                state[key].extend(val)

            # assign new values
            else:
                state[key] = val

    return state


# total nodes
builder.add_node("segmentation_node" , segmentation_node1) 
builder.add_node("classification_node" , classification_node2)
builder.add_node("memory_reader_node" , memory_reader) 
builder.add_node("memory_writer_node" , memory_writer , is_async=True) 
builder.add_node("router_node", router_node , is_async=True)
builder.add_node("final_answer" , final_answer_node)

#segmentation -> classification
builder.add_edge(START , "segmentation_node")
builder.add_edge("segmentation_node" , "classification_node")

# classification -> routing to memory_write parallel with || memory_read
builder.add_edge("classification_node" , "router_node") 
builder.add_edge("router_node", "final_answer") 

# final answer
builder.add_edge("final_answer" , END)

graph =  builder.compile()

# from PIL import Image as PILImage
# from IPython.display import Image, display
# image_data = graph.get_graph().draw_mermaid_png()
# with open("task_router_graph.png", "wb") as f:
#     f.write(image_data)
# img = PILImage.open("task_router_graph.png")
# img.show()

