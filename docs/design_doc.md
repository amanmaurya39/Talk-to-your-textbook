# Design Document — Talk To Your Textbook

**Student:** Aman Kumar  
**Problem Code:** I2  
**Segment:** Foundations of Applied Machine Learning  
**Date:** 26 June 2026  

---

## What Am I Building?

A RAG-based (Retrieval-Augmented Generation) document Q&A application. 
A user uploads any PDF textbook or document and asks natural language 
questions. The system retrieves the most relevant passages and returns 
answers with exact page citations using Google Gemini.

---

## The Problem It Solves

Students waste hours searching through 300+ page textbooks to find 
specific concepts. Ctrl+F only matches exact keywords. This app 
understands meaning — ask "explain backpropagation" and it finds 
the right page even if the word "backpropagation" isn't there.

---

## Who Is It For?

- College students studying from PDF textbooks
- Researchers reading long research papers  
- Anyone who needs to extract information from documents quickly

---

## Tech Stack

| Component | Choice | Why |
|---|---|---|
| PDF Parsing | PyMuPDF | Fast, gives page numbers per block |
| Chunking | LangChain RecursiveCharacterTextSplitter | Handles overlap cleanly |
| Embeddings | Google text-embedding-004 | Free with Google AI Studio key |
| Vector Store | ChromaDB | Zero setup, runs locally, persistent |
| Retrieval | Hybrid (dense + BM25) | Better than dense-only |
| LLM | Google Gemini | Free tier, strong instruction following |
| UI | Streamlit | Fast to build and deploy |
| Hosting | Streamlit Community Cloud | Free, one-click deploy |

---

## Architecture (How Data Flows)

PDF Upload → PyMuPDF parses pages → LangChain splits into chunks
→ Google embeds each chunk → ChromaDB stores vectors
→ User asks question → Query embedded → Hybrid search
→ Top 5 chunks retrieved → Gemini generates cited answer
→ Streamlit displays answer + source pages

---

## What I Will Build in 5 Weeks

- **Week 1:** PDF parsing, embedding, ChromaDB, basic Streamlit UI ✅
- **Week 2:** Hybrid retrieval, proper citations, end-to-end working
- **Week 3:** Mini-extension (compare 2 documents), tests, ADRs
- **Week 4:** Deployment, evaluation (20 Q&A pairs), README polish
- **Week 5:** Final submission, Loom video, resume bullets

---

## Mini-Extension Plan

Compare Two Documents — upload 2 PDFs and ask what each says 
about a topic. System retrieves from both and answers side by side 
with citations from each source.

---

## Known Risks

| Risk | Mitigation |
|---|---|
| Scanned PDFs have no extractable text | Warn user, recommend text-based PDFs |
| Google API rate limits on free tier | Add retry logic in Week 2 |
| Large PDFs slow to embed | Show progress bar, process in batches |