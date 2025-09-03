import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load env vars from backend/.env
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

deployment_name = os.getenv("GRAPHRAG_LLM_MODEL", "gpt-5-chat")
endpoint = os.getenv("GRAPHRAG_API_BASE", "https://gpt4-assistants-api.openai.azure.com/")
api_key = os.getenv("GRAPHRAG_API_KEY")
api_version = "2024-02-15-preview"
serpapi_api_key = os.getenv("SERPAPI_API_KEY")
