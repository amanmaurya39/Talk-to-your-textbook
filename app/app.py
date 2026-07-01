"""Main application module."""
import streamlit as st
import os

from src.ingest import load_pdf, chunk_pages
from src.embed import embed_and_store
from src.retrieve import hybrid_retrieve
from src.generate import generate_answer

# Page config
st.set_page_config(
    page_title="Talk To Your Textbook",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Talk To Your Textbook")
st.caption("Upload any PDF and ask questions — answers come with page citations.")

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.header("📄 Upload Your PDF")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload any textbook, notes, or document"
    )
    
    if uploaded_file:
        # Save uploaded file temporarily
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        
        with st.spinner("📖 Reading and indexing your PDF..."):
            pages = load_pdf(temp_path)
            chunks = chunk_pages(pages)
            embed_and_store(chunks)
            st.session_state["pdf_ready"] = True
            st.session_state["pdf_name"] = uploaded_file.name
        
        st.success(f"✅ Ready!\n\n📄 {len(pages)} pages\n🧩 {len(chunks)} chunks indexed")
        os.remove(temp_path)
    
    st.divider()
    st.markdown("**How it works:**")
    st.markdown("1. Upload a PDF")
    st.markdown("2. Ask any question")
    st.markdown("3. Get answers with page numbers")

# ── Main Area ─────────────────────────────────────────────
if st.session_state.get("pdf_ready"):
    st.subheader(f"Asking about: {st.session_state.get('pdf_name', 'your document')}")
    
    query = st.text_input(
        "💬 Ask a question:",
        placeholder="e.g. What is gradient descent? How does backpropagation work?"
    )
    
    if query:
        with st.spinner("🔍 Searching and generating answer..."):
            chunks = hybrid_retrieve(query, top_k=5)
            result = generate_answer(query, chunks)
        
        # Show answer
        st.subheader("Answer")
        st.write(result["answer"])
        
        # Show sources
        with st.expander("📖 View Source Passages"):
            for i, src in enumerate(result["sources"]):
                st.markdown(f"**Source {i+1} — Page {src['page']}**")
                st.caption(src["snippet"])
                st.divider()
else:
    # Empty state
    st.info("👈 Upload a PDF from the sidebar to get started.")
    st.markdown("""
    ### What can you ask?
    - *"What is supervised learning?"*
    - *"Explain the difference between overfitting and underfitting"*
    - *"What are the steps in gradient descent?"*
    
    The app will find the answer in your document and tell you exactly which page it came from.
    """)