"""Generation module."""
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a helpful study assistant that answers questions about documents.

STRICT RULES:
1. Answer ONLY using the context chunks provided below.
2. After every fact or sentence, cite the page like this: [Page X]
3. If the answer is not found in the context, respond with exactly:
   "I don't have enough information in this document to answer that."
4. Never make up information.
5. Be clear and concise.
"""

def generate_answer(query: str, chunks: list) -> dict:
    """Send query + retrieved chunks to GPT-4o-mini, get cited answer"""
    client = OpenAI()
    
    # Build context string from chunks
    context = ""
    for chunk in chunks:
        context += f"\n--- Page {chunk['page_number']} ---\n{chunk['text']}\n"
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0  # deterministic — important for citations
    )
    
    answer = response.choices[0].message.content
    
    return {
        "answer": answer,
        "sources": [
            {
                "page": c["page_number"],
                "snippet": c["text"][:200] + "..."
            }
            for c in chunks
        ]
    }
