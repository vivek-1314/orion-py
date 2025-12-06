import requests
from dotenv import load_dotenv
import os

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_URL = "https://api.jina.ai/v1/embeddings"

def embed_text(text: str) -> list[float]:
    """
    Generate embedding using Jina's v3 model.
    Same format as tested in Postman.
    """

    payload = {
        "model": "jina-embeddings-v3",
        "input": text
    }

    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(JINA_URL, json=payload, headers=headers)
    response.raise_for_status()   # throws error if API fails

    data = response.json()
    vector = data["data"][0]["embedding"]

    return vector