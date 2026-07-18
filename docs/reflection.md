# Reflection — Talk To Your Textbook

**Student:** Aman Kumar | **Problem:** I2 | **Duration:** 22 Jun – 23 Jul 2026

---

## Section 1: What I Built (200-300 words)

Talk To Your Textbook is a RAG-based document Q&A application built 
for students who need to extract specific information from large PDF 
textbooks without reading hundreds of pages. A user uploads any PDF 
and asks questions in plain English — the system returns grounded 
answers with exact page citations.

The core pipeline: PyMuPDF parses the PDF page by page → LangChain 
splits text into 400-token chunks → Google text-embedding-004 embeds 
each chunk → ChromaDB stores the vectors → hybrid retrieval (dense + 
BM25) finds the most relevant chunks → Google Gemini generates a 
cited answer.

The mini-extension adds multi-document comparison — upload two PDFs 
and ask what each says about a topic. The system retrieves from both 
collections separately and asks Gemini to compare with citations from 
each source using [Doc A, Page X] and [Doc B, Page Y] notation.

---

## Section 2: What I Learned About the Tools (300-400 words)

**PyMuPDF** — Much more than a PDF reader. It gives you page numbers 
per text block, which is critical for citations. Most RAG tutorials 
skip this and just dump all text into one string, losing page info.

**ChromaDB** — Deceptively simple. Three lines of code to store and 
query vectors. The PersistentClient saves to disk so embeddings 
survive restarts — this matters for development speed. Switching to 
EphemeralClient for cloud deployment was the key learning.

**Google Gemini** — The model name is tier-dependent. You can't just 
pick "gemini-1.5-flash" and expect it to work — you must call 
list_models() to see what your API key actually has access to. 
Temperature=0 is essential for consistent citations.

**Hybrid Retrieval** — BM25 is from 1994 but still adds real value 
alongside modern embeddings. Dense search finds semantic matches; 
BM25 catches exact terminology. Together they're consistently better 
than either alone.

**Streamlit** — Fast to build but has quirks. Session state must be 
initialized explicitly. The blank white page error was caused by 
silent import failures — wrapping everything in try/except with 
st.error() surfaces errors on screen.

---

## Section 3: What I Learned About Myself (300-400 words)

**Harder than expected:** Getting the API key situation right. I 
started with what I thought was an OpenAI key but it was actually 
a Google AI Studio key. This caused a 401 error on Week 1. The fix 
was straightforward once identified, but it taught me to always 
verify API key types before writing code around them.

**Easier than expected:** The RAG pipeline itself. Once I understood 
the flow (parse → chunk → embed → store → retrieve → generate), 
each step was a well-defined coding task. The conceptual complexity 
was higher than the implementation complexity.

**What I enjoyed most:** Debugging. Specifically the process of 
adding try/except blocks that surface errors in the Streamlit UI 
instead of silently crashing. Seeing a red error box with a clear 
message is genuinely satisfying.

**What I didn't enjoy:** Writing documentation while building. I 
kept wanting to code more and document later. The ADRs felt like 
overhead during Week 2 but became genuinely useful when my mentor 
asked "why ChromaDB?" — I had a complete written answer ready.

**Schedule:** I worked well during structured weeks but struggled 
on days without a clear task. The day-by-day plan helped enormously.

---

## Section 4: What I'd Do Differently (200-300 words)

**Test with a real PDF from Day 1.** I wasted Week 1 testing with 
a 1-page offer letter that had almost no text. The moment I switched 
to actual lecture notes, everything worked. I'd pick a proper test 
PDF before writing a single line of code.

**Call list_models() before hardcoding any model name.** I lost 2 
hours to a 404 error because gemini-1.5-flash wasn't available on 
my API tier. One command would have told me what to use.

**Plan for cloud deployment from Week 1.** ChromaDB's PersistentClient 
works locally but not on Streamlit Cloud. If I'd known this earlier, 
I'd have built the local/cloud switch from the start instead of 
retrofitting it in Week 4.

---

## Section 5: What's Next — The 3rd Year Plan (200-300 words)

In 3rd year, this project becomes a multi-document enterprise RAG 
system. The 2nd year version proves the core pipeline works. The 
3rd year version adds:

- Persistent user document libraries (no re-upload each session)
- Support for 4+ document types (DOCX, HTML, EPUB, not just PDF)
- Fine-tuned embedding model on academic text
- Proper evaluation harness with automated Ragas scoring
- Multi-tenant deployment so classmates can use their own accounts

By the 3rd year internship, this maps directly to the E3 problem 
(Enterprise RAG) — same pipeline, production-grade engineering.
