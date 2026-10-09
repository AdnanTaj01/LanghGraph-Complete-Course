
import os
from typing import TypedDict, Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

# .env file se API key load karo
load_dotenv()

# Grok LLM setup
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


class State(TypedDict):
    message: str
    intent: str
    response: str


# DECIDING: Grok user ka intent identify karega
def classify(state: State) -> dict:
    prompt = f"""
    You are a customer support intent classifier.

    Read the user message and choose exactly ONE category:
    refund, shipping, or human.

    Rules:
    - refund: money back, refund, returned payment
    - shipping: delivery, shipment, order tracking
    - human: anything else

    Return ONLY the category name.
    Do not explain your answer.

    User message: {state["message"]}
    """

    result = llm.invoke(prompt)
    intent = result.content.strip().lower()

    # Invalid model output ho to safe fallback
    if intent not in {"refund", "shipping", "human"}:
        intent = "human"

    print("Grok classified intent:", intent)
    return {"intent": intent}


# ROUTING: agla node select karo
def route(
    state: State,
) -> Literal["refund", "shipping", "human"]:
    return state["intent"]


# DOING: har node apna kaam karega
def refund(state: State) -> dict:
    return {
        "response": "Your refund request will be reviewed."
    }


def shipping(state: State) -> dict:
    return {
        "response": "We are checking your delivery status."
    }


def human(state: State) -> dict:
    return {
        "response": "Your request will be sent to human support."
    }


# Graph build karo
builder = StateGraph(State)

builder.add_node("classify", classify)
builder.add_node("refund", refund)
builder.add_node("shipping", shipping)
builder.add_node("human", human)

builder.add_edge(START, "classify")

builder.add_conditional_edges("classify", route)

builder.add_edge("refund", END)
builder.add_edge("shipping", END)
builder.add_edge("human", END)

graph = builder.compile()


# Agent ko test karo
result = graph.invoke({
    "message": "Where is my delivery?",
    "intent": "",
    "response": "",
})

print("\nFinal response:", result["response"])

print("\n===== GRAPH =====")
print(graph.get_graph().draw_mermaid())