"""Compare module."""
import chromadb
import google.generativeai as genai
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT, ".env"))

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=api_key)
# Use persistent locally, in-memory on cloud
if os.getenv("STREAMLIT_CLOUD"):
    chroma_client = chromadb.EphemeralClient()
else:
    chroma_client = chromadb.PersistentClient(path=os.path.join(ROOT, "chroma_db"))


def retrieve_from_collection(query: str, collection_name: str, top_k: int = 4) -> list:
    """Retrieve chunks from a specific named collection"""
    try:
        collection = chroma_client.get_collection(collection_name)
    except Exception:
        return []

    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=query
    )
    query_embedding = result["embedding"]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k * 2, collection.count())
    )

    candidates = []
    for i in range(len(results["documents"][0])):
        candidates.append({
            "text": results["documents"][0][i],
            "page_number": results["metadatas"][0][i]["page_number"],
            "source": results["metadatas"][0][i]["source"],
            "dense_score": 1 - results["distances"][0][i]
        })

    if candidates:
        corpus = [c["text"] for c in candidates]
        tokenized = [doc.lower().split() for doc in corpus]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())
        for i, c in enumerate(candidates):
            c["bm25_score"] = float(scores[i])
            c["final_score"] = c["dense_score"] + (c["bm25_score"] * 0.3)
        candidates = sorted(candidates, key=lambda x: x["final_score"], reverse=True)

    return candidates[:top_k]


def compare_documents(query: str, doc_a_name: str, doc_b_name: str) -> dict:
    """Compare two documents on a topic using Gemini"""
    model = genai.GenerativeModel("gemini-2.5-flash")

    chunks_a = retrieve_from_collection(query, collection_name="doc_a", top_k=4)
    chunks_b = retrieve_from_collection(query, collection_name="doc_b", top_k=4)

    context_a = "\n".join(
        [f"[Doc A, Page {c['page_number']}]: {c['text']}" for c in chunks_a]
    ) or "No relevant content found."

    context_b = "\n".join(
        [f"[Doc B, Page {c['page_number']}]: {c['text']}" for c in chunks_b]
    ) or "No relevant content found."

    prompt = f"""You are comparing two documents on a specific topic.
Document A: "{doc_a_name}"
Document B: "{doc_b_name}"

RULES:
1. Use ONLY the context below — no outside knowledge.
2. Cite sources like [Doc A, Page X] or [Doc B, Page Y].
3. Structure your answer in 3 parts:
   - What Document A says (with citations)
   - What Document B says (with citations)
   - Key similarities and differences

=== Document A ===
{context_a}

=== Document B ===
{context_b}

Question: {query}

Comparison:"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=1500
            )
        )
        answer = response.text
    except Exception as e:
        answer = f"Error generating comparison: {str(e)}"

    return {
        "answer": answer,
        "doc_a_sources": [
            {"page": c["page_number"], "snippet": c["text"][:200] + "..."}
            for c in chunks_a
        ],
        "doc_b_sources": [
            {"page": c["page_number"], "snippet": c["text"][:200] + "..."}
            for c in chunks_b
        ]
    }