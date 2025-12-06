from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

raw_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

llm = raw_llm 