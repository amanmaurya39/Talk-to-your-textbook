"""Embedding generation module."""
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
import os

# ── Load .env from project root ───────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT, ".env"))

# ── Configure Google API ──────────────────────────────────
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")
genai.configure(api_key=api_key)

# ── ChromaDB client ───────────────────────────────────────
# Use persistent locally, in-memory on cloud
if os.getenv("STREAMLIT_CLOUD"):
    chroma_client = chromadb.EphemeralClient()
else:
    chroma_client = chromadb.PersistentClient(path=os.path.join(ROOT, "chroma_db"))


import time
from google.api_core.exceptions import ResourceExhausted

def get_embedding(text: str) -> list:
    """Get embedding for a single text using Gemini embeddings with rate-limit retries."""
    for attempt in range(6):
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text
            )
            return result["embedding"]
        except ResourceExhausted:
            wait_time = (2 ** attempt) + 1
            print(f"⚠️ Rate limit hit. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
        except Exception as e:
            if "429" in str(e):
                wait_time = (2 ** attempt) + 1
                print(f"⚠️ Rate limit hit (429). Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise e
    raise RuntimeError("Failed to generate embedding: Rate limit exceeded after multiple retries.")


def embed_and_store(chunks: list, collection_name: str = "textbook"):
    """
    Embed all chunks using Google and store them in ChromaDB.
    Deletes old collection first so re-uploading a new PDF starts fresh.
    """

    # Delete old collection if it exists
    try:
        chroma_client.delete_collection(collection_name)
        print(f"🗑️  Deleted old collection: {collection_name}")
    except Exception:
        pass  # No old collection — that's fine

    # Create fresh collection
    collection = chroma_client.create_collection(name=collection_name)
    texts = [c["text"] for c in chunks]

    print(f"⏳ Embedding {len(chunks)} chunks using Gemini embeddings...")

    all_embeddings = []
    for i, text in enumerate(texts):
        embedding = get_embedding(text)
        all_embeddings.append(embedding)
        if (i + 1) % 10 == 0:
            print(f"   Embedded {i + 1}/{len(texts)} chunks")

    # Store everything in ChromaDB
    collection.add(
        documents=texts,
        embeddings=all_embeddings,
        metadatas=[
            {
                "page_number": c["page_number"],
                "source": c["source"]
            }
            for c in chunks
        ],
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    print(f"✅ Successfully stored {len(chunks)} chunks in ChromaDB collection '{collection_name}'")