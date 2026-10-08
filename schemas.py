import os
from dotenv import load_dotenv
from typing import Annotated, TypedDict
import operator

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import (
    StateGraph,
    START,
    END,
    add_messages,
)

load_dotenv()
# ============================================================
# PART 1 — Reducers
# ============================================================

class ReducerState(TypedDict):
    items: Annotated[list[str], operator.add]
    attempts: Annotated[int, operator.add]
    status: str


def try_once(state: ReducerState) -> dict:
    return {
        "items": ["tried"],
        "attempts": 1,
        "status": "done",
    }


# ============================================================
# PART 2 — Reducer Graph
# ============================================================

builder = StateGraph(ReducerState)

builder.add_node("try_once", try_once)

builder.add_edge(START, "try_once")
builder.add_edge("try_once", END)

reducer_graph = builder.compile()


# Existing state + new node output
result = reducer_graph.invoke({
    "items": ["first"],
    "attempts": 2,
    "status": "pending",
})

print("===== REDUCER RESULT =====")
print(result)


# ============================================================
# PART 3 — Message Types
# ============================================================

print("\n===== MESSAGE TYPES =====")

system_message = SystemMessage(
    content="You are a helpful AI assistant."
)

human_message = HumanMessage(
    content="Hello, my name is Adnan."
)

ai_message = AIMessage(
    content="Hello Adnan! Nice to meet you."
)

print("System:", system_message)
print("Human:", human_message)
print("AI:", ai_message)


# ============================================================
# PART 4 — Conversation State with add_messages
# ============================================================

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    log: Annotated[list[str], operator.add]
    turns: Annotated[int, operator.add]


# ============================================================
# PART 5 — Gemini LLM
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash"
)


# ============================================================
# PART 6 — Chat Node
# ============================================================

def chat(state: ChatState) -> dict:
    reply = llm.invoke(state["messages"])

    return {
        "messages": [reply]
    }


# ============================================================
# PART 7 — Log Node
# ============================================================

def log(state: ChatState) -> dict:
    return {
        "log": ["turn done"],
        "turns": 1,
    }


# ============================================================
# PART 8 — Build Chat Graph
# ============================================================

chat_builder = StateGraph(ChatState)

chat_builder.add_node("chat", chat)
chat_builder.add_node("log", log)

chat_builder.add_edge(START, "chat")
chat_builder.add_edge("chat", "log")
chat_builder.add_edge("log", END)

chat_graph = chat_builder.compile()


# ============================================================
# PART 9 — Run Chat Graph
# ============================================================

result = chat_graph.invoke({
    "messages": [
        HumanMessage(content="Hi, I'm Adnan. Say hello to me.")
    ],
    "log": [],
    "turns": 0,
})


# ============================================================
# PART 10 — Print Result
# ============================================================

print("\n===== CHAT RESULT =====")

print("\nMessages:")

for message in result["messages"]:
    print(
        f"{message.__class__.__name__}: "
        f"{message.content}"
    )

print("\nLog:")
print(result["log"])

print("\nTurns:")
print(result["turns"])


# ============================================================
# PART 11 — Draw Graph
# ============================================================

print("\n===== GRAPH =====")

print(chat_graph.get_graph().draw_mermaid())