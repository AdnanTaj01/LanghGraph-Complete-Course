
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite import SqliteSaver


# ==========================================
# 1. Load API key
# ==========================================

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY .env file mein nahi mili.")


# ==========================================
# 2. Configure Groq LLM
# ==========================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# ==========================================
# 3. Define Graph State
# ==========================================

class State(TypedDict):
    draft: str
    approved: bool
    feedback: str
    sent: bool


# ==========================================
# 4. Draft Node
# ==========================================

def draft_email(state: State) -> dict:
    print("\n[Draft Node] AI email bana raha hai...")

    prompt = (
        "Write a professional apology email to a customer. "
        "The email must contain exactly two sentences. "
        "Return only the email, without a subject or explanation."
    )

    if state["feedback"]:
        prompt += (
            f"\nImprove the email using this feedback: "
            f"{state['feedback']}"
        )

    response = llm.invoke(prompt)

    print("[Draft Node] Email draft ready.")

    return {
        "draft": response.content,
        "approved": False,
        "sent": False
    }


# ==========================================
# 5. Approval Node
# ==========================================

def approval(state: State) -> dict:
    print("\n[Approval Node] Human approval required.")

    # Graph yahan pause hoga.
    # Resume hone par is node ki execution dobara start hogi.
    decision = interrupt({
        "question": "Approve this email? Reply yes or no.",
        "proposal": state["draft"]
    })

    decision = str(decision).strip().lower()

    return {
        "approved": decision == "yes"
    }


# ==========================================
# 6. Route According to Decision
# ==========================================

def route_after_approval(state: State) -> str:
    if state["approved"]:
        return "send"

    return "revise"


# ==========================================
# 7. Revise Node
# ==========================================

def revise_email(state: State) -> dict:
    print("\n[Revise Node] Email revise hoga...")

    return {
        "feedback": "Make the apology email shorter and clearer.",
        "approved": False
    }


# ==========================================
# 8. Send Node
# ==========================================

def send_email(state: State) -> dict:
    # Demo only: asal email send nahi hoti.
    print("\n========== EMAIL SENT ==========")
    print("SENT:", state["draft"])
    print("================================")

    return {
        "sent": True
    }


# ==========================================
# 9. Build the Graph
# ==========================================

builder = StateGraph(State)

builder.add_node("draft", draft_email)
builder.add_node("approval", approval)
builder.add_node("revise", revise_email)
builder.add_node("send", send_email)

builder.add_edge(START, "draft")
builder.add_edge("draft", "approval")

builder.add_conditional_edges(
    "approval",
    route_after_approval,
    {
        "send": "send",
        "revise": "revise"
    }
)

builder.add_edge("revise", "draft")
builder.add_edge("send", END)


# ==========================================
# 10. SQLite Checkpointer + Menu
# ==========================================

def main():
    with SqliteSaver.from_conn_string(
        "checkpoints.db"
    ) as checkpointer:

        graph = builder.compile(
            checkpointer=checkpointer
        )

        print("\n===== MODULE 07: HUMAN-IN-THE-LOOP =====")

        while True:
            print("\n1. Start a new approval")
            print("2. Resume a paused approval")
            print("3. View saved graph state")
            print("4. Exit")

            choice = input("\nSelect option: ").strip()

            if choice == "1":
                thread_id = input(
                    "Enter a NEW thread ID: "
                ).strip()

                if not thread_id:
                    print("Thread ID khali nahi ho sakti.")
                    continue

                config = {
                    "configurable": {
                        "thread_id": thread_id
                    }
                }

                # Existing thread ko accidentally overwrite ya
                # mix karne se bachne ke liye unique ID use karo.
                existing = graph.get_state(config)

                if existing.values:
                    print(
                        "Is thread mein pehle se state hai. "
                        "Naya thread ID use karo."
                    )
                    continue

                result = graph.invoke(
                    {
                        "draft": "",
                        "approved": False,
                        "feedback": "",
                        "sent": False
                    },
                    config=config
                )

                print("\nGraph response:", result)

                if result.get("__interrupt__"):
                    print("\nGraph pause ho gaya.")
                    print("Human ko proposal review karna hai.")
                    print("Paused node:", graph.get_state(config).next)

            elif choice == "2":
                thread_id = input(
                    "Wohi thread ID enter karo: "
                ).strip()

                if not thread_id:
                    print("Thread ID khali nahi ho sakti.")
                    continue

                config = {
                    "configurable": {
                        "thread_id": thread_id
                    }
                }

                snapshot = graph.get_state(config)

                if not snapshot.values or not snapshot.next:
                    print(
                        "Is thread mein koi paused graph nahi mila."
                    )
                    continue

                print("\nCurrent draft:")
                print(snapshot.values.get("draft", ""))

                decision = input(
                    "\nApprove? Type yes or no: "
                ).strip().lower()

                if decision not in ("yes", "no"):
                    print("Sirf yes ya no likho.")
                    continue

                result = graph.invoke(
                    Command(resume=decision),
                    config=config
                )

                if result.get("__interrupt__"):
                    print("\nGraph dobara pause ho gaya.")
                    print("Naya proposal:")
                    print(result["__interrupt__"])
                    print("Ab option 2 se dobara resume karo.")

                else:
                    print("\nGraph execution complete.")
                    print("Sent:", result.get("sent", False))

            elif choice == "3":
                thread_id = input(
                    "Thread ID enter karo: "
                ).strip()

                config = {
                    "configurable": {
                        "thread_id": thread_id
                    }
                }

                snapshot = graph.get_state(config)

                if not snapshot.values:
                    print("Koi saved state nahi mili.")
                    continue

                print("\nSaved state:")
                print(snapshot.values)

                print("\nNext node(s):")
                print(snapshot.next)

            elif choice == "4":
                print("Program exit ho raha hai.")
                break

            else:
                print("Invalid option. 1 se 4 select karo.")


if __name__ == "__main__":
    main()