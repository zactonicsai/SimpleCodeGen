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
  <meta charset="UTF-8" />
  <title>Address Form</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-slate-100 flex items-center justify-center p-4">
  <div class="w-full max-w-xl bg-white shadow-lg rounded-2xl p-8">
    <h1 class="text-2xl font-bold text-slate-800 mb-2">Address Form</h1>
    <p class="text-slate-500 mb-6 text-sm">
      Enter your address information and submit.
    </p>

    <!-- Alert / Status -->
    <div id="statusBox" class="hidden mb-4 text-sm rounded-md px-3 py-2"></div>

    <form id="addressForm" class="space-y-4">
      <!-- Name -->
      <div>
        <label for="fullName" class="block text-sm font-medium text-slate-700 mb-1">
          Full Name
        </label>
        <input
          id="fullName"
          name="fullName"
          type="text"
          required
          class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="Jane Doe"
        />
      </div>

      <!-- Street -->
      <div>
        <label for="street" class="block text-sm font-medium text-slate-700 mb-1">
          Street Address
        </label>
        <input
          id="street"
          name="street"
          type="text"
          required
          class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="123 Main St"
        />
      </div>

      <!-- City / State / Zip -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label for="city" class="block text-sm font-medium text-slate-700 mb-1">
            City
          </label>
          <input
            id="city"
            name="city"
            type="text"
            required
            class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Montgomery"
          />
        </div>
        <div>
          <label for="state" class="block text-sm font-medium text-slate-700 mb-1">
            State / Province
          </label>
          <input
            id="state"
            name="state"
            type="text"
            required
            class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="AL"
          />
        </div>
        <div>
          <label for="postalCode" class="block text-sm font-medium text-slate-700 mb-1">
            ZIP / Postal Code
          </label>
          <input
            id="postalCode"
            name="postalCode"
            type="text"
            required
            class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="36104"
          />
        </div>
      </div>

      <!-- Country -->
      <div>
        <label for="country" class="block text-sm font-medium text-slate-700 mb-1">
          Country
        </label>
        <input
          id="country"
          name="country"
          type="text"
          required
          class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="United States"
        />
      </div>

      <!-- Optional Email -->
      <div>
        <label for="email" class="block text-sm font-medium text-slate-700 mb-1">
          Email (optional)
        </label>
        <input
          id="email"
          name="email"
          type="email"
          class="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="you@example.com"
        />
      </div>

      <!-- Submit -->
      <div class="pt-2 flex items-center gap-3">
        <button
          type="submit"
          id="submitBtn"
          class="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          Submit Address
        </button>
        <span id="loadingText" class="hidden text-xs text-slate-500">
          Sending...
        </span>
      </div>
    </form>
  </div>

  <script>
    const form = document.getElementById('addressForm');
    const statusBox = document.getElementById('statusBox');
    const submitBtn = document.getElementById('submitBtn');
    const loadingText = document.getElementById('loadingText');

    function setStatus(message, type = 'success') {
      statusBox.textContent = message;
      statusBox.classList.remove('hidden');
      statusBox.classList.remove(
        'bg-red-100',
        'text-red-700',
        'border-red-300',
        'bg-green-100',
        'text-green-700',
        'border-green-300'
      );

      if (type === 'error') {
        statusBox.classList.add('bg-red-100', 'text-red-700', 'border', 'border-red-300');
      } else {
        statusBox.classList.add('bg-green-100', 'text-green-700', 'border', 'border-green-300');
      }
    }

    function setLoading(isLoading) {
      submitBtn.disabled = isLoading;
      loadingText.classList.toggle('hidden', !isLoading);
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      setLoading(true);
      statusBox.classList.add('hidden');

      const data = {
        fullName: form.fullName.value.trim(),
        street: form.street.value.trim(),
        city: form.city.value.trim(),
        state: form.state.value.trim(),
        postalCode: form.postalCode.value.trim(),
        country: form.country.value.trim(),
        email: form.email.value.trim() || null,
      };

      try {
        const response = await fetch('/api/address', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const errText = await response.text();
          throw new Error(errText || 'Failed to submit address');
        }

        setStatus('Address submitted successfully!', 'success');
        form.reset();
      } catch (err) {
        console.error(err);
        setStatus('Error: ' + err.message, 'error');
      } finally {
        setLoading(false);
      }
    });
  </script>
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
