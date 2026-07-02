"""Main application module."""
import streamlit as st
import sys
import os

# Fix path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ingest import load_pdf, chunk_pages
from src.embed import embed_and_store
from src.retrieve import hybrid_retrieve
from src.generate import generate_answer

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="Talk To Your Textbook",
    page_icon="📚",
    layout="wide"
)

# ── Session State Init ────────────────────────────────────
if "pdf_ready" not in st.session_state:
    st.session_state["pdf_ready"] = False
if "pdf_name" not in st.session_state:
    st.session_state["pdf_name"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ── Header ────────────────────────────────────────────────
st.title("📚 Talk To Your Textbook")
st.caption("Upload any PDF and ask questions — get answers with exact page citations.")

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("📄 Your Document")
    
    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type="pdf",
        help="Upload any textbook, notes, or document"
    )
    
    if uploaded_file:
        if uploaded_file.name != st.session_state["pdf_name"]:
            # New file uploaded — process it
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
            
            with st.spinner("📖 Reading and indexing PDF..."):
                try:
                    pages = load_pdf(temp_path)
                    chunks = chunk_pages(pages)
                    embed_and_store(chunks)
                    
                    st.session_state["pdf_ready"] = True
                    st.session_state["pdf_name"] = uploaded_file.name
                    st.session_state["chat_history"] = []  # reset chat
                    st.session_state["total_pages"] = len(pages)
                    st.session_state["total_chunks"] = len(chunks)
                    
                except Exception as e:
                    st.error(f"❌ Error processing PDF: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    
    # Show stats if PDF is loaded
    if st.session_state["pdf_ready"]:
        st.success(f"✅ {st.session_state['pdf_name']}")
        col1, col2 = st.columns(2)
        col1.metric("Pages", st.session_state.get("total_pages", "-"))
        col2.metric("Chunks", st.session_state.get("total_chunks", "-"))
        
        st.divider()
        if st.button("🗑️ Clear & Upload New PDF"):
            st.session_state["pdf_ready"] = False
            st.session_state["pdf_name"] = ""
            st.session_state["chat_history"] = []
            st.rerun()
    
    st.divider()
    st.markdown("**How it works:**")
    st.markdown("1. 📤 Upload a PDF")
    st.markdown("2. 💬 Ask any question")
    st.markdown("3. 📖 Get answers with page numbers")
    st.markdown("4. 🔍 Check the source passages")

# ── Main Chat Area ────────────────────────────────────────
if st.session_state["pdf_ready"]:
    
    # Show chat history
    for chat in st.session_state["chat_history"]:
        with st.chat_message("user"):
            st.write(chat["question"])
        with st.chat_message("assistant"):
            st.write(chat["answer"])
            with st.expander("📖 Source Pages"):
                for src in chat["sources"]:
                    st.markdown(f"**Page {src['page']}**")
                    st.caption(src["snippet"])
                    st.divider()
    
    # Question input
    query = st.chat_input("Ask a question about your document...")
    
    if query:
        # Show user message
        with st.chat_message("user"):
            st.write(query)
        
        # Generate answer
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching document..."):
                try:
                    chunks = hybrid_retrieve(query, top_k=5)
                    result = generate_answer(query, chunks)
                    
                    st.write(result["answer"])
                    
                    with st.expander("📖 Source Pages"):
                        for src in result["sources"]:
                            st.markdown(f"**Page {src['page']}**")
                            st.caption(src["snippet"])
                            st.divider()
                    
                    # Save to chat history
                    st.session_state["chat_history"].append({
                        "question": query,
                        "answer": result["answer"],
                        "sources": result["sources"]
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")

else:
    # Empty state — no PDF uploaded yet
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📤 Upload")
        st.markdown("Upload any PDF — textbook, notes, research paper")
    
    with col2:
        st.markdown("### 💬 Ask")
        st.markdown("Type any question in natural language")
    
    with col3:
        st.markdown("### 📖 Cite")
        st.markdown("Get answers with exact page numbers")
    
    st.divider()
    st.markdown("### 💡 Example Questions You Can Ask")
    st.markdown("""
    - *"What is gradient descent?"*
    - *"Explain overfitting and underfitting"*  
    - *"What are the types of machine learning?"*
    - *"Summarise chapter 3"*
    - *"What does the author say about neural networks?"*
    """)
    st.info("👈 Upload a PDF from the sidebar to get started!")