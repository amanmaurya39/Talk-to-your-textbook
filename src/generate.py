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

# ── Gemini model ──────────────────────────────────────────
model = genai.GenerativeModel("gemini-2.5-flash")

# ── System prompt ─────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpful study assistant that answers questions strictly based on the provided document context.

RULES YOU MUST FOLLOW:
1. Answer ONLY using the context chunks provided below. Do not use any outside knowledge.
2. After every sentence or fact you state, add a citation like this: [Page X]
3. If the answer cannot be found in the context, respond with exactly this:
   "I don't have enough information in this document to answer that."
4. Never guess or make up information.
5. Keep your answer clear, concise, and well-structured.
6. If the question asks to summarize, provide a bullet-point summary with page citations.
"""


def generate_answer(query: str, chunks: list) -> dict:
    """
    Send the user query + retrieved chunks to Gemini.
    Returns the answer text + source page snippets for display.

    Args:
        query: The user's question
        chunks: List of retrieved chunks from hybrid_retrieve()

    Returns:
        dict with keys:
            - answer: str (Gemini's response with [Page X] citations)
            - sources: list of {page, snippet} for display in UI
    """

    # ── Build context string from chunks ──────────────────
    context = ""
    for chunk in chunks:
        context += f"\n--- Page {chunk['page_number']} ---\n{chunk['text']}\n"

    # ── Build full prompt ─────────────────────────────────
    full_prompt = f"""{SYSTEM_PROMPT}

========== DOCUMENT CONTEXT ==========
{context}
=======================================

Question: {query}

Answer:"""

    # ── Call Gemini ───────────────────────────────────────
    try:
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,   # deterministic — important for factual citation answers
                max_output_tokens=1024
            )
        )
        answer = response.text

    except Exception as e:
        answer = f"Error generating answer: {str(e)}"

    # ── Build source list for UI display ──────────────────
    sources = []
    for chunk in chunks:
        sources.append({
            "page": chunk["page_number"],
            "snippet": chunk["text"][:250] + "..."  # show first 250 chars as preview
        })

    return {
        "answer": answer,
        "sources": sources
    }