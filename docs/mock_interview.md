# Mock Interview Q&A

**Q1: What is RAG and why did you use it?**
RAG stands for Retrieval-Augmented Generation. Instead of asking an 
LLM to answer from memory (which causes hallucination), RAG first 
retrieves relevant passages from your document, then passes them to 
the LLM as context. The LLM can only answer from what you give it — 
making answers grounded and citable. I used it because the problem 
requires trustworthy, verifiable answers from a specific document.

**Q2: Why hybrid retrieval over just using ChromaDB?**
Dense retrieval (ChromaDB) finds semantically similar passages — 
great for meaning. But BM25 catches exact keyword matches — great 
for terminology. A student asking about "gradient descent" benefits 
from both: dense finds related optimization concepts, BM25 finds 
exact mentions. Combined they outperform either alone.

**Q3: How did you handle the Google vs OpenAI API confusion?**
I started the project assuming I had an OpenAI key. On Day 1, a 401 
error revealed it was a Google AI Studio key. I migrated the entire 
stack — embeddings, generation, and model selection — to Google's 
library in 2 hours. I documented this in ADR-002 as a conscious 
architectural decision with full trade-off analysis.

**Q4: What are the limitations of your system?**
Three main ones: scanned PDFs have no extractable text so the system 
fails silently — I added validation to catch this early. ChromaDB's 
PersistentClient doesn't work on Streamlit Cloud — I added an 
EphemeralClient fallback. And there's no memory across sessions — 
users must re-upload their PDF each visit.

**Q5: How would you scale this for 1000 users?**
Replace ChromaDB with Qdrant Cloud for multi-tenant vector storage. 
Add a user authentication layer. Cache embeddings by document hash 
so the same PDF isn't re-embedded by multiple users. Move from 
Streamlit to FastAPI + React for better scalability. Add a queue 
for embedding large PDFs asynchronously.
