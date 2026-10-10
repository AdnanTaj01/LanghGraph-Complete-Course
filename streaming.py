
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    name: str
    greeting: str
    final_message: str


def greet(state: State) -> dict:
    print("   [Inside greet node]")
    return {
        "greeting": f"Hello, {state['name']}!"
    }


def make_final(state: State) -> dict:
    print("   [Inside make_final node]")
    return {
        "final_message": (
            f"{state['greeting']} Welcome to LangGraph."
        )
    }


builder = StateGraph(State)

builder.add_node("greet", greet)
builder.add_node("make_final", make_final)

builder.add_edge(START, "greet")
builder.add_edge("greet", "make_final")
builder.add_edge("make_final", END)

graph = builder.compile()


inputs = {
    "name": "Adnan",
    "greeting": "",
    "final_message": ""
}

print("\n========== USING INVOKE ==========")

result = graph.invoke(inputs)
print("Final result:", result["final_message"])


print("\n========== USING STREAM UPDATES ==========")

for chunk in graph.stream(inputs, stream_mode="updates"):
    print("Stream event:", chunk)

print("\n========== USING STREAM VALUES ==========")

for chunk in graph.stream(inputs, stream_mode="values"):
    print("Stream event:", chunk)