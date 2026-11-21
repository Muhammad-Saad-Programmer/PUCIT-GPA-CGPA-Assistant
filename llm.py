import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from groq import AsyncGroq
from langchain.chat_models import init_chat_model

load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = "groq:openai/gpt-oss-120b"

@asynccontextmanager
async def open_model():
    """Keep the Groq client on the event loop that uses it."""
    async with AsyncGroq(api_key=GROQ_API_KEY) as client:
        yield init_chat_model(
            GROQ_MODEL, api_key=GROQ_API_KEY, async_client=client.chat.completions
        )
