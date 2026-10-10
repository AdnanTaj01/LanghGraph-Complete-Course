
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY .env file mein nahi mili.")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

prompt = "Explain LangGraph in 5 simple sentences for a beginner."

print("Model is generating its answer:\n")

for chunk in llm.stream(prompt):
    if chunk.content:
        print(chunk.content, end="", flush=True)

print("\n\nStreaming finished.")
