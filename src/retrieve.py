"""Retrieval module."""
import chromadb
from openai import OpenAI
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
chroma_client = chromadb.PersistentClient(path="./chroma_db")

def embed_query(query: str) -> list:
	"""Embed a single query string"""
	response = client.embeddings.create(
		input=[query],
		model="text-embedding-3-small"
	)
	return response.data[0].embedding

def hybrid_retrieve(query: str, collection_name: str = "textbook", top_k: int = 5) -> list:
	"""
	Hybrid retrieval = Dense (ChromaDB) + Sparse (BM25)
	Better than dense-only because it catches exact keyword matches too
	"""
	collection = chroma_client.get_collection(collection_name)
    
	# Step 1 — Dense retrieval (semantic similarity)
	query_embedding = embed_query(query)
	results = collection.query(
		query_embeddings=[query_embedding],
		n_results=top_k * 2  # get more, then re-rank
	)
    
	# Build candidate list
	candidates = []
	for i in range(len(results["documents"][0])):
		candidates.append({
			"text": results["documents"][0][i],
			"page_number": results["metadatas"][0][i]["page_number"],
			"source": results["metadatas"][0][i]["source"],
			"dense_score": 1 - results["distances"][0][i]  # convert distance to similarity
		})
    
	# Step 2 — BM25 re-ranking on top of dense results
	corpus = [c["text"] for c in candidates]
	tokenized = [doc.lower().split() for doc in corpus]
	bm25 = BM25Okapi(tokenized)
	bm25_scores = bm25.get_scores(query.lower().split())
    
	# Step 3 — Combine scores and rank
	for i, candidate in enumerate(candidates):
		candidate["bm25_score"] = float(bm25_scores[i])
		candidate["final_score"] = candidate["dense_score"] + (bm25_scores[i] * 0.3)
    
	ranked = sorted(candidates, key=lambda x: x["final_score"], reverse=True)
	return ranked[:top_k]
