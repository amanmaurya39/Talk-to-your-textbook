# Talk To Your Textbook — 3rd Year Extension Roadmap

## What this project is today
A working RAG pipeline: upload PDF → hybrid retrieval → 
Gemini generates cited answers. Mini-extension compares two docs.
Deployed on Streamlit Cloud. Evaluated on 20+ Q&A pairs.

## The arc: where this could be by May 2027
A multi-tenant, multi-format enterprise RAG system that handles 
PDFs, DOCX, HTML, and EPUB — with persistent document libraries, 
automated evaluation, and fine-tuned embeddings for academic text.

## 3rd Year Semester Plan (Aug 2026 - Dec 2026)

### Milestone 1 (Aug-Sep): Persistent Document Library
- What: Users save document collections, no re-upload each session
- Tools: PostgreSQL for metadata, Qdrant Cloud for vectors
- Time: 6 hours/week
- Done: User logs in, sees their saved PDFs, asks questions immediately

### Milestone 2 (Oct-Nov): Multi-Format Support
- What: DOCX, HTML, EPUB support alongside PDF
- Tools: Unstructured.io, python-docx, BeautifulSoup
- Time: 5 hours/week
- Done: Upload any of 4 formats, same Q&A experience

### Milestone 3 (Nov-Dec): Automated Evaluation
- What: Ragas scoring on every answer automatically
- Tools: Ragas, LangSmith for tracing
- Time: 4 hours/week
- Done: Every answer gets faithfulness + relevance scores logged

## 3rd Year Internship Plan (Jun-Jul 2027)
This becomes the E3 Enterprise RAG problem — same pipeline, 
production engineering: multi-tenant, monitored, evaluated, 
with a fine-tuned embedding model on domain-specific text.

## Risks
- Qdrant Cloud free tier has storage limits at scale
- Fine-tuning embeddings requires labeled domain data
- Multi-tenancy adds auth complexity I haven't handled yet