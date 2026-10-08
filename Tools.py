from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import (
    StateGraph,
    START,
    END,
    add_messages,
)

from langgraph.prebuilt import (
    ToolNode,
    tools_condition,
)

from typing import Annotated, TypedDict


# ============================================
# 1. Load .env
# ============================================

load_dotenv()


# ============================================
# 2. State
# ============================================

class State(TypedDict):
    messages: Annotated[list, add_messages]


# ============================================
# 3. Tool
# ============================================

@tool
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b


# ============================================
# 4. Gemini Model
# ============================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash"
)


# ============================================
# 5. Bind Tool to Gemini
# ============================================

tools = [add]

llm_with_tools = llm.bind_tools(tools)


# ============================================
# 6. Agent Node
# ============================================

def agent(state: State):
    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }


# ============================================
# 7. Tool Node
# ============================================

tool_node = ToolNode(tools)


# ============================================
# 8. Create Graph
# ============================================

builder = StateGraph(State)


# Add nodes
builder.add_node("agent", agent)
builder.add_node("tools", tool_node)


# START → agent
builder.add_edge(
    START,
    "agent"
)


# Agent → tools OR END
builder.add_conditional_edges(
    "agent",
    tools_condition
)


# tools → agent
builder.add_edge(
    "tools",
    "agent"
)


# ============================================
# 9. Compile
# ============================================

graph = builder.compile()


# ============================================
# 10. Run Agent
# ============================================

result = graph.invoke({
    "messages": [
        {
            "role": "user",
            "content": "What is 2 + 3?"
        }
    ]
})


# ============================================
# 11. Print Trace
# ============================================

print("\n===== AGENT TRACE =====")

for message in result["messages"]:

    print(
        "\n",
        type(message).__name__,
        "->",
        message.content or message.tool_calls
    )

    # ============================================
    # 12. Show Graph
    # ============================================

print("\n===== GRAPH =====")

print(graph.get_graph().draw_mermaid())

mermaid = graph.get_graph().draw_mermaid()

with open("graph.md", "w", encoding="utf-8") as file:
    file.write("```mermaid\n")
    file.write(mermaid)
    file.write("\n```")

print("Graph saved to graph.md")