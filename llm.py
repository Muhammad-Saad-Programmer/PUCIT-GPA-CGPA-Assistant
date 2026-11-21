from langchain.chat_models import init_chat_model
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = "groq:openai/gpt-oss-120b"

llm = init_chat_model(GROQ_MODEL, api_key=GROQ_API_KEY)

