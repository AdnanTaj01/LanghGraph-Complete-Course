############################################# fan out (Yeh sirf tasks distribute karta hai. using Send) ################################################

# import os
# import operator
# from typing import TypedDict, Annotated

# from dotenv import load_dotenv
# from langchain_groq import ChatGroq

# from langgraph.graph import StateGraph, START, END
# from langgraph.types import Send


# # ==========================================
# # 1. Load API key
# # ==========================================

# load_dotenv()

# if not os.getenv("GROQ_API_KEY"):
#     raise ValueError("GROQ_API_KEY .env file mein nahi mili.")


# # ==========================================
# # 2. Configure the LLM
# # ==========================================

# llm = ChatGroq(
#     model="openai/gpt-oss-120b",
#     temperature=0
# )


# # ==========================================
# # 3. Define the shared state
# # ==========================================

# class State(TypedDict):
#     products: list[str]
#     descriptions: Annotated[list[str], operator.add]
#     combined: str


# # ==========================================
# # 4. Prepare node
# # ==========================================

# def prepare(state: State) -> dict:
#     print("Preparing product list...")
#     print("Total products:", len(state["products"]))

#     return {}


# # ==========================================
# # 5. Fan-out function
# # ==========================================

# def fan_out(state: State):
#     return [
#         Send("describe", {"product": product})
#         for product in state["products"]
#     ]


# # ==========================================
# # 6. Specialist node
# # ==========================================

# def describe(state: dict) -> dict:
#     product = state["product"]

#     print(f"Creating description for: {product}")

#     prompt = (
#         f"Write one short sentence describing the product "
#         f"{product}. Do not invent exact ingredients, prices, "
#         f"or health claims. Keep it simple."
#     )

#     response = llm.invoke(prompt)

#     description = f"{product}: {response.content.strip()}"

#     return {
#         "descriptions": [description]
#     }


# # ==========================================
# # 7. Combine node
# # ==========================================

# def combine(state: State) -> dict:
#     print("\nCombining all product descriptions...")

#     bullet_list = "\n".join(
#         f"- {description}"
#         for description in state["descriptions"]
#     )

#     return {
#         "combined": bullet_list
#     }


# # ==========================================
# # 8. Build the graph
# # ==========================================

# builder = StateGraph(State)

# builder.add_node("prepare", prepare)
# builder.add_node("describe", describe)
# builder.add_node("combine", combine)

# builder.add_edge(START, "prepare")

# builder.add_conditional_edges(
#     "prepare",
#     fan_out
# )

# builder.add_edge("describe", "combine")
# builder.add_edge("combine", END)

# graph = builder.compile()


# # ==========================================
# # 9. Run the graph
# # ==========================================

# if __name__ == "__main__":

#     result = graph.invoke({
#         "products": [
#             "Lays",
#             "Milk Pack",
#             "Sufi Soap",
#             "Sooper Biscuit",
#             "Lemon Max"
#         ],
#         "descriptions": [],
#         "combined": ""
#     })

#     print("\n========== FINAL RESULT ==========")
#     print(result["combined"])

#     print("\nDescriptions generated:", len(result["descriptions"]))


###################################### supervisor (Yeh direct tasks bhejta hai) ######################################################################



# import os
# from typing import TypedDict, Literal

# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# from langgraph.graph import StateGraph, START, END

# load_dotenv()

# if not os.getenv("GROQ_API_KEY"):
#     raise ValueError("GROQ_API_KEY .env file mein nahi mili.")

# llm = ChatGroq(
#     model="openai/gpt-oss-120b",
#     temperature=0
# )


# # Shared memory: tamam agents isi state ko use karenge.
# class State(TypedDict):
#     task: str
#     research: str
#     draft: str
#     review: str
#     next: str
#     steps: int


# # Manager: decide karega agla agent kaun hoga.
# def supervisor(state: State) -> dict:
#     if state["steps"] >= 6:
#         choice = "done"

#     elif not state["research"]:
#         choice = "researcher"

#     elif not state["draft"]:
#         choice = "writer"

#     elif not state["review"]:
#         choice = "reviewer"

#     else:
#         choice = "done"

#     print(f"\nSupervisor selected: {choice}")

#     return {
#         "next": choice,
#         "steps": state["steps"] + 1
#     }


# # Agent 1: information prepare karega.
# def researcher(state: State) -> dict:
#     print("Researcher is working...")

#     prompt = f"""
#     Prepare 4 useful facts for this task:
#     {state['task']}

#     Keep the information short and beginner-friendly.
#     Do not invent statistics or fake sources.
#     """

#     response = llm.invoke(prompt)

#     return {"research": response.content}


# # Agent 2: information se draft banayega.
# def writer(state: State) -> dict:
#     print("Writer is working...")

#     prompt = f"""
#     User task: {state['task']}

#     Information:
#     {state['research']}

#     Write a clear, short answer using this information.
#     """

#     response = llm.invoke(prompt)

#     return {"draft": response.content}


# # Agent 3: draft ko review karega.
# def reviewer(state: State) -> dict:
#     print("Reviewer is checking the draft...")

#     prompt = f"""
#     Review this draft for clarity, relevance, and unsupported claims.

#     Original task:
#     {state['task']}

#     Draft:
#     {state['draft']}

#     Give brief feedback. If it is acceptable, say APPROVED.
#     Do not claim you verified facts against external sources.
#     """

#     response = llm.invoke(prompt)

#     return {"review": response.content}


# # Supervisor ke decision ke mutabiq next node select hoga.
# def route_next(
#     state: State
# ) -> Literal["researcher", "writer", "reviewer", "done"]:
#     return state["next"]


# # Graph create karna.
# builder = StateGraph(State)

# builder.add_node("supervisor", supervisor)
# builder.add_node("researcher", researcher)
# builder.add_node("writer", writer)
# builder.add_node("reviewer", reviewer)

# builder.add_edge(START, "supervisor")

# builder.add_conditional_edges(
#     "supervisor",
#     route_next,
#     {
#         "researcher": "researcher",
#         "writer": "writer",
#         "reviewer": "reviewer",
#         "done": END
#     }
# )

# # Har worker ka kaam khatam hone par manager ke paas wapas jao.
# builder.add_edge("researcher", "supervisor")
# builder.add_edge("writer", "supervisor")
# builder.add_edge("reviewer", "supervisor")

# graph = builder.compile()


# if __name__ == "__main__":
#     result = graph.invoke({
#         "task": "Explain Artificial Intelligence to a beginner.",
#         "research": "",
#         "draft": "",
#         "review": "",
#         "next": "",
#         "steps": 0
#     })

#     print("\n========== FINAL DRAFT ==========")
#     print(result["draft"])

#     print("\n========== REVIEW ==========")
#     print(result["review"])

#     print("\nTotal supervisor decisions:", result["steps"])



########################################## sub-graphs ######################################################################

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# Child graph ki state
class ResearchState(TypedDict):
    topic: str
    analysis: str
    summary: str


# Child graph node 1
def analyze(state: ResearchState) -> dict:
    print("Child graph: analyzing topic...")

    return {
        "analysis": (
            f"{state['topic']} ko samajhne ke liye "
            "uske meaning aur uses identify karo."
        )
    }


# Child graph node 2
def summarize(state: ResearchState) -> dict:
    print("Child graph: creating summary...")

    return {
        "summary": f"Summary: {state['analysis']}"
    }


# Child graph build karo
child_builder = StateGraph(ResearchState)

child_builder.add_node("analyze", analyze)
child_builder.add_node("summarize", summarize)

child_builder.add_edge(START, "analyze")
child_builder.add_edge("analyze", "summarize")
child_builder.add_edge("summarize", END)

research_graph = child_builder.compile()


# Parent graph ki state
class ParentState(TypedDict):
    topic: str
    result: str


# Parent node child graph ko call karega
def run_research(state: ParentState) -> dict:
    print("Parent graph: calling research subgraph...")

    child_result = research_graph.invoke({
        "topic": state["topic"],
        "analysis": "",
        "summary": ""
    })

    return {"result": child_result["summary"]}


# Parent graph build karo
parent_builder = StateGraph(ParentState)

parent_builder.add_node("research", run_research)

parent_builder.add_edge(START, "research")
parent_builder.add_edge("research", END)

parent_graph = parent_builder.compile()


if __name__ == "__main__":
    result = parent_graph.invoke({
        "topic": "Artificial Intelligence",
        "result": ""
    })

    print("\nFinal result:")
    print(result["result"])

    