from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    name: str
    greeting: str


def greet(state: State) -> dict:
    return {
        "greeting": f"Hello, {state['name']}!"
    }


def shout(state: State) -> dict:
    return {
        "greeting": state["greeting"].upper()
    }


builder = StateGraph(State)

builder.add_node("greet", greet)
builder.add_node("shout", shout)

builder.add_edge(START, "greet")
builder.add_edge("greet", "shout")
builder.add_edge("shout", END)

graph = builder.compile()


result = graph.invoke({
    "name": "Adnan"
})

print(result)

print(graph.get_graph().draw_mermaid())

mermaid = graph.get_graph().draw_mermaid()

with open("graph.md", "w", encoding="utf-8") as file:
    file.write("```mermaid\n")
    file.write(mermaid)
    file.write("\n```")

print("Graph saved to graph.md")