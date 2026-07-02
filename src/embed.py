"""Embedding generation module."""
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
chroma_client = chromadb.PersistentClient(path="./chroma_db")


def get_openai_client() -> OpenAI:
    """Create an OpenAI client after environment variables are loaded."""
    return OpenAI()


def embed_and_store(chunks: list, collection_name: str = "textbook"):
    """Embed chunks with OpenAI and store in ChromaDB"""
    client = get_openai_client()

    # Delete old collection if exists (fresh start)
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    collection = chroma_client.create_collection(name=collection_name)
    texts = [c["text"] for c in chunks]

    print(f"⏳ Embedding {len(chunks)} chunks...")

    # Embed in batches of 100 (API limit)
    all_embeddings = []
    for i in range(0, len(texts), 100):
        batch = texts[i:i + 100]
        response = client.embeddings.create(
            input=batch,
            model="text-embedding-3-small"
        )
        all_embeddings.extend([e.embedding for e in response.data])
        print(f"  Embedded {min(i + 100, len(texts))}/{len(texts)}")

    # Store in ChromaDB
    collection.add(
        documents=texts,
        embeddings=all_embeddings,
        metadatas=[{
            "page_number": c["page_number"],
            "source": c["source"]
        } for c in chunks],
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )
    print(f"✅ Stored {len(chunks)} chunks in ChromaDB")
