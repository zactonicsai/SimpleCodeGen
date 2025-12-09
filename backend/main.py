import os
from typing import List, Optional

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import chromadb
from chromadb.config import Settings

# ---------- ChromaDB SETUP ----------

CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "code_snippets")

client = chromadb.PersistentClient(path=CHROMA_PATH, settings=Settings(allow_reset=True))
collection = client.get_or_create_collection(name=COLLECTION_NAME)


def seed_chroma_if_empty():
    existing = collection.count()
    if existing > 0:
        return

    docs = [
        # Simple Tailwind HTML template
        """Basic Tailwind HTML page:
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Tailwind Starter</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gray-100 flex items-center justify-center">
  <div class="bg-white shadow rounded p-6 max-w-lg w-full">
    <h1 class="text-2xl font-bold mb-4">Hello Tailwind</h1>
    <button class="px-4 py-2 bg-blue-600 text-white rounded">Click me</button>
  </div>
</body>
</html>
""",
        # Simple JS fetch() API call template
        """Simple JavaScript fetch POST example:

async function callApi() {
  const response = await fetch('http://localhost:8000/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: 'Create a simple Node.js Express server',
      code_type: 'node'
    })
  });
  const data = await response.json();
  console.log(data);
}
""",
        # Simple Python FastAPI template
        """Python FastAPI sample:

from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello World"}
""",
    ]

    metadatas = [
        {"lang": "html", "description": "Basic Tailwind HTML page template"},
        {"lang": "javascript", "description": "JS fetch example for POST API"},
        {"lang": "python", "description": "Simple FastAPI example"},
    ]

    ids = ["doc-html-tailwind", "doc-js-fetch", "doc-python-fastapi"]

    collection.add(
        documents=docs,
        metadatas=metadatas,
        ids=ids,
    )


seed_chroma_if_empty()

# ---------- OLLAMA + API SETUP ----------

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")  # adjust to your model


class GenerateRequest(BaseModel):
    prompt: str
    code_type: Optional[str] = None
    n_results: int = 3


class GenerateResponse(BaseModel):
    output: str
    used_context: List[str]


app = FastAPI(title="Chroma + Ollama Code Generator")

# Allow frontend on localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local dev; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate_code(req: GenerateRequest):
    # 1) Retrieve similar docs from Chroma
    results = collection.query(
        query_texts=[req.prompt],
        n_results=req.n_results,
    )

    contexts = results.get("documents", [[]])[0] if results.get("documents") else []
    contexts_text = "\n\n---\n\n".join(contexts)

    # 2) Build prompt for Ollama
    system_message = (
        "You are an expert code generator. "
        "You receive a user request and some example code snippets as context. "
        "Use the context as inspiration, but generate fresh, clean code."
    )

    user_prompt = f"""User request:
{req.prompt}

Code type: {req.code_type or "unspecified"}

Relevant snippets from the knowledge base:
{contexts_text}

Now generate the best possible code for the user. 
Respond with ONLY code and minimal comments.
"""

    # 3) Call Ollama chat API
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
    except Exception as e:
        content = f"Error calling Ollama: {e}"

    return GenerateResponse(output=content, used_context=contexts)
