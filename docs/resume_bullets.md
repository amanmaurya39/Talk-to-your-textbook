# Resume Bullets — Talk To Your Textbook

## Project Bullet
Built **Talk To Your Textbook**, a RAG-based PDF Q&A system using 
Google text-embedding-004, ChromaDB hybrid retrieval (BM25 + dense), 
and Google Gemini — deployed on Streamlit Cloud with page-level citations

## Technical Bullet
Implemented **hybrid retrieval pipeline** combining ChromaDB dense 
search and BM25 keyword matching, improving answer relevance over 
dense-only retrieval; evaluated on 20+ hand-authored Q&A pairs

## Extension Bullet  
Extended single-document RAG to **multi-document comparison** — 
system retrieves from two separate vector collections and generates 
side-by-side cited answers using [Doc A, Page X] notation
