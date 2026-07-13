import chromadb
import google.generativeai as genai
from rank_bm25 import BM25Okapi
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
chroma_client = chromadb.PersistentClient(path=os.path.join(ROOT, "chroma_db"))


def embed_query(query: str) -> list:
    """Embed a single query string using Gemini embeddings."""
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=query
    )
    return result["embedding"]


def hybrid_retrieve(query: str, collection_name: str = "textbook", top_k: int = 5) -> list:
    """
    Hybrid retrieval = Dense (Google embeddings in ChromaDB) + Sparse (BM25 keyword)

    Steps:
    1. Embed the query using Google
    2. Get top (top_k * 2) results from ChromaDB using dense similarity
    3. Re-rank those results using BM25 keyword matching
    4. Combine both scores and return top_k final results

    This is better than dense-only because:
    - Dense catches meaning/semantics ("what is gradient descent" finds "optimization algorithm")
    - BM25 catches exact keywords ("gradient descent" finds "gradient descent" directly)
    """

    # ── Step 1: Get collection ────────────────────────────
    try:
        collection = chroma_client.get_collection(collection_name)
    except Exception:
        raise ValueError(f"Collection '{collection_name}' not found. Please upload a PDF first.")

    # ── Step 2: Dense retrieval ───────────────────────────
    query_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k * 2, collection.count())  # don't request more than exists
    )

    # Build candidate list from dense results
    candidates = []
    for i in range(len(results["documents"][0])):
        candidates.append({
            "text": results["documents"][0][i],
            "page_number": results["metadatas"][0][i]["page_number"],
            "source": results["metadatas"][0][i]["source"],
            "dense_score": 1 - results["distances"][0][i]  # convert distance → similarity
        })

    # ── Step 3: BM25 re-ranking ───────────────────────────
    corpus = [c["text"] for c in candidates]
    tokenized = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())

    # ── Step 4: Combine scores ────────────────────────────
    for i, candidate in enumerate(candidates):
        candidate["bm25_score"] = float(bm25_scores[i])
        # Weighted combination: dense (70%) + BM25 (30%)
        candidate["final_score"] = candidate["dense_score"] + (bm25_scores[i] * 0.3)

    # Sort by combined score, return top_k
    ranked = sorted(candidates, key=lambda x: x["final_score"], reverse=True)
    return ranked[:top_k]