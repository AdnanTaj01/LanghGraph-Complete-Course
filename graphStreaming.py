
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END


# ==================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==================================================

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError(
        "GROQ_API_KEY .env file mein nahi mili."
    )


# ==================================================
# 2. INITIALIZE LLM
# ==================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# ==================================================
# 3. DEFINE GRAPH STATE
# ==================================================

class State(TypedDict):
    topic: str
    answer: str


# ==================================================
# 4. DEFINE NODE
# ==================================================

def answer_node(state: State) -> dict:
    """
    AI se jawab generate karta hai.
    Printing aur UI handling is node ki responsibility nahi.
    """

    prompt = (
        f"Explain {state['topic']} to a beginner "
        "in 4 short sentences."
    )

    response = llm.invoke(prompt)

    return {
        "answer": response.content
    }


# ==================================================
# 5. BUILD LANGGRAPH
# ==================================================

builder = StateGraph(State)

builder.add_node(
    "answer_node",
    answer_node
)

builder.add_edge(
    START,
    "answer_node"
)

builder.add_edge(
    "answer_node",
    END
)

graph = builder.compile()


# ==================================================
# 6. PREPARE INPUT
# ==================================================

inputs = {
    "topic": "LangGraph",
    "answer": ""
}


# ==================================================
# 7. CONFIGURE RUN AND LANGSMITH TRACING
# ==================================================

config = {
    "run_name": "LangGraph_Token_Streaming",
    "tags": [
        "langgraph-course",
        "module-09",
        "development"
    ],
    "metadata": {
        "module": "09",
        "feature": "token-streaming",
        "version": "1.0"
    }
}


# ==================================================
# 8. STREAM GRAPH EVENTS
# ==================================================

def main():
    print("\n========== STREAMING STARTED ==========\n")

    try:
        for mode, chunk in graph.stream(
            inputs,
            config=config,
            stream_mode=["updates", "messages"]
        ):

            # ------------------------------------------
            # A. MODEL MESSAGE EVENTS
            # ------------------------------------------

            if mode == "messages":
                message_chunk, metadata = chunk

                # Sirf apne AI node ke message chunks
                if (
                    metadata.get("langgraph_node")
                    == "answer_node"
                ):
                    content = message_chunk.content

                    # Kuch model integrations content blocks
                    # ki list bhi return kar sakti hain.
                    if isinstance(content, str) and content:
                        print(
                            content,
                            end="",
                            flush=True
                        )

                    elif isinstance(content, list):
                        for block in content:
                            if (
                                isinstance(block, dict)
                                and block.get("type") == "text"
                            ):
                                print(
                                    block.get("text", ""),
                                    end="",
                                    flush=True
                                )

            # ------------------------------------------
            # B. GRAPH NODE UPDATES
            # ------------------------------------------

            elif mode == "updates":
                print("\n\n[GRAPH UPDATE]")
                print(chunk)

        print("\n\n========== STREAMING FINISHED ==========")

    except Exception as exc:
        print(f"\n\n[ERROR] Graph execution failed: {exc}")


# ==================================================
# 9. APPLICATION ENTRY POINT
# ==================================================

if __name__ == "__main__":
    main()
