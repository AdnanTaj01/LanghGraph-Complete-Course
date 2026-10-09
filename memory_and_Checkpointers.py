############################################ Memory and Checkpointers without DataBase ##########################################


# import os
# from typing import Annotated, TypedDict

# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_core.tools import tool
# from langgraph.graph import StateGraph, START, END, add_messages
# from langgraph.prebuilt import ToolNode, tools_condition
# from langgraph.checkpoint.memory import MemorySaver

# # Load environment variables
# load_dotenv()

# if not os.getenv("GROQ_API_KEY"):
#     raise ValueError("GROQ_API_KEY .env file mein nahi mili.")

# # Groq LLM setup
# llm = ChatGroq(
#     model="openai/gpt-oss-120b",
#     temperature=0,
# )


# # Tool: do numbers add karta hai
# @tool
# def add(a: int, b: int) -> int:
#     """Add two integers and return their sum."""
#     return a + b


# tools = [add]
# llm_with_tools = llm.bind_tools(tools)


# # Shared conversation state
# class State(TypedDict):
#     messages: Annotated[list, add_messages]


# # Agent node
# def agent(state: State) -> dict:
#     response = llm_with_tools.invoke(state["messages"])
#     return {"messages": [response]}


# # Tool execution node
# tool_node = ToolNode(tools)


# # Build graph
# builder = StateGraph(State)

# builder.add_node("agent", agent)
# builder.add_node("tools", tool_node)

# builder.add_edge(START, "agent")
# builder.add_conditional_edges("agent", tools_condition)
# builder.add_edge("tools", "agent")

# # Enable checkpointing
# memory = MemorySaver()
# graph = builder.compile(checkpointer=memory)


# # Thread 1: Adnan's conversation
# adnan_config = {
#     "configurable": {
#         "thread_id": "adnan-1"
#     }
# }

# print("\n===== TURN 1 =====")

# result1 = graph.invoke(
#     {
#         "messages": [
#             SystemMessage(
#                 content=(
#                     "You are a helpful math assistant. "
#                     "Use the add tool for calculations. "
#                     "Remember earlier results in this conversation."
#                 )
#             ),
#             HumanMessage(content="Calculate 2 + 3 using the add tool.")
#         ]
#     },
#     config=adnan_config,
# )

# for message in result1["messages"]:
#     if message.type == "tool":
#         print("Tool result:", message.content)

# print("Assistant:", result1["messages"][-1].content)


# print("\n===== TURN 2 =====")

# result2 = graph.invoke(
#     {
#         "messages": [
#             HumanMessage(
#                 content="Double the result from before using the add tool."
#             )
#         ]
#     },
#     config=adnan_config,
# )

# print("Assistant:", result2["messages"][-1].content)


# print("\n===== SAVED CONVERSATION =====")

# snapshot = graph.get_state(adnan_config)

# for message in snapshot.values["messages"]:
#     print(f"{message.type}: {message.content}")


# print("\n===== THREAD 2: BOB =====")

# bob_config = {
#     "configurable": {
#         "thread_id": "bob-1"
#     }
# }

# result_bob = graph.invoke(
#     {
#         "messages": [
#             SystemMessage(
#                 content=(
#                     "You are a helpful math assistant. "
#                     "Use the add tool for calculations. "
#                     "Do not assume you know facts from other conversations."
#                 )
#             ),
#             HumanMessage(
#                 content="Double the result from before using the add tool."
#             )
#         ]
#     },
#     config=bob_config,
# )

# print("Bob's assistant:", result_bob["messages"][-1].content)

# print("\n===== BOB'S SAVED STATE =====")
# print(graph.get_state(bob_config).values["messages"])


#################################################### Memory and Checkpointers with SQLite Database ##########################################################


import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver


# ==========================================
# 1. Load API key
# ==========================================

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError(
        "GROQ_API_KEY nahi mili. Apni .env file check karo."
    )


# ==========================================
# 2. Configure Groq LLM
# ==========================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# ==========================================
# 3. Create a Tool
# ==========================================

@tool
def add(a: int, b: int) -> int:
    """Add two integers and return their sum."""
    return a + b


tools = [add]

# LLM ko available tools batana
llm_with_tools = llm.bind_tools(tools)


# ==========================================
# 4. Define Graph State
# ==========================================

class State(TypedDict):
    messages: Annotated[list, add_messages]


# ==========================================
# 5. Create Agent Node
# ==========================================

def agent(state: State) -> dict:
    response = llm_with_tools.invoke(state["messages"])

    return {
        "messages": [response]
    }


# ==========================================
# 6. Build LangGraph
# ==========================================

builder = StateGraph(State)

builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")

builder.add_conditional_edges(
    "agent",
    tools_condition
)

builder.add_edge("tools", "agent")


# ==========================================
# 7. SQLite Checkpointing
# ==========================================

SYSTEM_MESSAGE = SystemMessage(
    content=(
        "You are a helpful math assistant. "
        "Use the add tool whenever a calculation requires addition. "
        "Use previous messages to understand references to earlier results. "
        "If a previous result is unavailable, ask the user to provide it."
    )
)


def main():
    # SQLite file automatically create ho jayegi
    # agar ye file pehle se nahi hai.
    with SqliteSaver.from_conn_string(
        "checkpoints.db"
    ) as checkpointer:

        # Graph ki memory SQLite ke saath connect karo
        graph = builder.compile(
            checkpointer=checkpointer
        )

        print("\n===== LangGraph SQLite Memory =====")
        print("1. Adnan ki conversation")
        print("2. Bob ki separate conversation")
        print("3. Adnan ki saved memory dekho")
        print("4. Adnan ki memory history dekho")
        print("5. Exit")

        while True:
            choice = input("\nApna option select karo: ").strip()

            # --------------------------------------
            # OPTION 1: Adnan ki conversation
            # --------------------------------------
            if choice == "1":

                config = {
                    "configurable": {
                        "thread_id": "adnan-1"
                    }
                }

                user_text = input(
                    "Adnan ka message likho: "
                ).strip()

                if not user_text:
                    print("Message khali nahi hona chahiye.")
                    continue

                # Pehli conversation ho to system message add karo.
                # Existing conversation mein sirf naya message add hoga.
                snapshot = graph.get_state(config)

                if snapshot.values:
                    messages = [HumanMessage(content=user_text)]
                else:
                    messages = [
                        SYSTEM_MESSAGE,
                        HumanMessage(content=user_text)
                    ]

                result = graph.invoke(
                    {"messages": messages},
                    config=config
                )

                print("\nAssistant:")

                # Latest assistant response display karo
                for message in reversed(result["messages"]):
                    if message.type == "ai" and message.content:
                        print(message.content)
                        break

            # --------------------------------------
            # OPTION 2: Bob ki separate conversation
            # --------------------------------------
            elif choice == "2":

                config = {
                    "configurable": {
                        "thread_id": "bob-1"
                    }
                }

                user_text = input(
                    "Bob ka message likho: "
                ).strip()

                if not user_text:
                    print("Message khali nahi hona chahiye.")
                    continue

                snapshot = graph.get_state(config)

                if snapshot.values:
                    messages = [HumanMessage(content=user_text)]
                else:
                    messages = [
                        SYSTEM_MESSAGE,
                        HumanMessage(content=user_text)
                    ]

                result = graph.invoke(
                    {"messages": messages},
                    config=config
                )

                print("\nBob ke assistant ka response:")

                for message in reversed(result["messages"]):
                    if message.type == "ai" and message.content:
                        print(message.content)
                        break

            # --------------------------------------
            # OPTION 3: Adnan ki saved memory
            # --------------------------------------
            elif choice == "3":

                config = {
                    "configurable": {
                        "thread_id": "adnan-1"
                    }
                }

                snapshot = graph.get_state(config)

                if not snapshot.values:
                    print("Adnan ki koi saved conversation nahi mili.")
                    continue

                print("\n===== Adnan ki Saved Messages =====")

                for message in snapshot.values["messages"]:
                    content = message.content

                    if isinstance(content, str) and content.strip():
                        print(f"{message.type.upper()}: {content}")

                    elif isinstance(content, list):
                        print(f"{message.type.upper()}: {content}")

                    # Tool-call messages mein content khali ho sakta hai.
                    # Unhein skip kar rahe hain taake output readable rahe.

            # --------------------------------------
            # OPTION 4: Adnan ki checkpoint history
            # --------------------------------------
            elif choice == "4":

                config = {
                    "configurable": {
                        "thread_id": "adnan-1"
                    }
                }

                history = list(
                    graph.get_state_history(config)
                )

                if not history:
                    print("Abhi koi checkpoint history nahi hai.")
                    continue

                print("\n===== Checkpoint History =====")

                for index, snapshot in enumerate(history, start=1):
                    print(f"\nCheckpoint {index}")
                    print("Next nodes:", snapshot.next)
                    print("Checkpoint config:", snapshot.config)

                    messages = snapshot.values.get("messages", [])

                    if messages:
                        print("Messages saved:", len(messages))

            # --------------------------------------
            # OPTION 5: Exit
            # --------------------------------------
            elif choice == "5":
                print("Program band ho raha hai.")
                break

            else:
                print("Invalid option. 1 se 5 tak select karo.")


if __name__ == "__main__":
    main()