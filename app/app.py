# pyrefly: ignore [missing-import]
import streamlit as st
import sys
import os

# ── Fix: tell Python where to find src/ ──────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ingest import load_pdf, chunk_pages
from src.embed import embed_and_store
from src.retrieve import hybrid_retrieve
from src.generate import generate_answer
from src.compare import compare_documents

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="Talk To Your Textbook",
    page_icon="📚",
    layout="wide"
)

# ── Session State Init ────────────────────────────────────
keys_to_init = {
    "pdf_ready": False,
    "pdf_name": "",
    "chat_history": [],
    "total_pages": 0,
    "total_chunks": 0,
    "doc_a_ready": False,
    "doc_a_name": "",
    "total_pages_a": 0,
    "total_chunks_a": 0,
    "doc_b_ready": False,
    "doc_b_name": "",
    "total_pages_b": 0,
    "total_chunks_b": 0,
    "compare_chat_history": []
}

for key, default_val in keys_to_init.items():
    if key not in st.session_state:
        st.session_state[key] = default_val

# ── Header ────────────────────────────────────────────────
st.title("📚 Talk To Your Textbook")
st.caption("Upload any PDF and ask questions — get answers with exact page citations.")

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("📄 Your Document")
    compare_mode = st.toggle("🔀 Compare Two Documents", value=False)

    if not compare_mode:
        uploaded_file = st.file_uploader(
            "Upload a PDF",
            type="pdf",
            key="pdf_uploader",
            help="Upload any textbook, lecture notes, or research paper"
        )

        # ── Process uploaded PDF ──────────────────────────────
        if uploaded_file:
            if uploaded_file.name != st.session_state["pdf_name"]:

                # Check file size — warn if too large
                file_size_mb = uploaded_file.size / (1024 * 1024)
                if file_size_mb > 50:
                    st.warning(f"⚠️ Large file ({file_size_mb:.1f}MB). Processing may take a while.")

                # Save file temporarily to disk
                temp_path = os.path.join(ROOT, f"temp_{uploaded_file.name}")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.read())

                with st.spinner("📖 Reading and indexing PDF..."):
                    try:
                        # Step 1 — Parse PDF
                        pages = load_pdf(temp_path)

                        # Step 2 — Check if PDF has real text
                        if len(pages) == 0:
                            st.error("❌ No text found in this PDF.")
                            st.info("💡 This PDF may be a scanned image. Please use a text-based PDF.")
                            os.remove(temp_path)
                            st.stop()

                        # Step 3 — Warn if very few pages
                        if len(pages) < 3:
                            st.warning(
                                f"⚠️ Only {len(pages)} page(s) found. "
                                "Answers may be limited. Try a longer document."
                            )

                        # Step 4 — Chunk pages
                        chunks = chunk_pages(pages)

                        # Step 5 — Embed and store in ChromaDB
                        embed_and_store(chunks, collection_name="textbook")

                        # Step 6 — Update session state
                        st.session_state["pdf_ready"] = True
                        st.session_state["pdf_name"] = uploaded_file.name
                        st.session_state["chat_history"] = []  # reset chat for new PDF
                        st.session_state["total_pages"] = len(pages)
                        st.session_state["total_chunks"] = len(chunks)

                    except Exception as e:
                        st.error(f"❌ Error processing PDF: {e}")
                        st.info("💡 Try a different PDF — make sure it has real text, not scanned images.")

                    finally:
                        # Always clean up temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        # ── Show PDF stats if loaded ──────────────────────────
        if st.session_state["pdf_ready"]:
            st.success(f"✅ {st.session_state['pdf_name']}")

            col1, col2 = st.columns(2)
            col1.metric("Pages", st.session_state["total_pages"])
            col2.metric("Chunks", st.session_state["total_chunks"])

            st.divider()

            if st.button("🗑️ Clear & Upload New PDF", key="clear_single"):
                st.session_state["pdf_ready"] = False
                st.session_state["pdf_name"] = ""
                st.session_state["chat_history"] = []
                st.session_state["total_pages"] = 0
                st.session_state["total_chunks"] = 0
                if "pdf_uploader" in st.session_state:
                    del st.session_state["pdf_uploader"]
                st.rerun()

    else:
        st.subheader("📄 Document A")
        uploaded_file_a = st.file_uploader(
            "Upload Document A",
            type="pdf",
            key="pdf_uploader_a",
            help="Upload the first document to compare"
        )
        if uploaded_file_a:
            if uploaded_file_a.name != st.session_state["doc_a_name"]:
                # Check file size — warn if too large
                file_size_mb = uploaded_file_a.size / (1024 * 1024)
                if file_size_mb > 50:
                    st.warning(f"⚠️ Large file ({file_size_mb:.1f}MB). Processing may take a while.")

                # Save file temporarily to disk
                temp_path = os.path.join(ROOT, f"temp_{uploaded_file_a.name}")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file_a.read())

                with st.spinner("📖 Reading and indexing Document A..."):
                    try:
                        # Step 1 — Parse PDF
                        pages = load_pdf(temp_path)

                        # Step 2 — Check if PDF has real text
                        if len(pages) == 0:
                            st.error("❌ No text found in Document A.")
                            os.remove(temp_path)
                            st.stop()

                        # Step 3 — Warn if very few pages
                        if len(pages) < 3:
                            st.warning(f"⚠️ Only {len(pages)} page(s) found in Document A.")

                        # Step 4 — Chunk pages
                        chunks = chunk_pages(pages)

                        # Step 5 — Embed and store in ChromaDB (collection: doc_a)
                        embed_and_store(chunks, collection_name="doc_a")

                        # Step 6 — Update session state
                        st.session_state["doc_a_ready"] = True
                        st.session_state["doc_a_name"] = uploaded_file_a.name
                        st.session_state["compare_chat_history"] = []  # reset chat
                        st.session_state["total_pages_a"] = len(pages)
                        st.session_state["total_chunks_a"] = len(chunks)

                    except Exception as e:
                        st.error(f"❌ Error processing Document A: {e}")

                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        if st.session_state["doc_a_ready"]:
            st.success(f"✅ Doc A: {st.session_state['doc_a_name']}")
            col1, col2 = st.columns(2)
            col1.metric("Pages", st.session_state["total_pages_a"])
            col2.metric("Chunks", st.session_state["total_chunks_a"])
            if st.button("🗑️ Clear Doc A", key="clear_a"):
                st.session_state["doc_a_ready"] = False
                st.session_state["doc_a_name"] = ""
                st.session_state["total_pages_a"] = 0
                st.session_state["total_chunks_a"] = 0
                if "pdf_uploader_a" in st.session_state:
                    del st.session_state["pdf_uploader_a"]
                st.rerun()

        st.subheader("📄 Document B")
        uploaded_file_b = st.file_uploader(
            "Upload Document B",
            type="pdf",
            key="pdf_uploader_b",
            help="Upload the second document to compare"
        )
        if uploaded_file_b:
            if uploaded_file_b.name != st.session_state["doc_b_name"]:
                # Check file size — warn if too large
                file_size_mb = uploaded_file_b.size / (1024 * 1024)
                if file_size_mb > 50:
                    st.warning(f"⚠️ Large file ({file_size_mb:.1f}MB). Processing may take a while.")

                # Save file temporarily to disk
                temp_path = os.path.join(ROOT, f"temp_{uploaded_file_b.name}")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file_b.read())

                with st.spinner("📖 Reading and indexing Document B..."):
                    try:
                        # Step 1 — Parse PDF
                        pages = load_pdf(temp_path)

                        # Step 2 — Check if PDF has real text
                        if len(pages) == 0:
                            st.error("❌ No text found in Document B.")
                            os.remove(temp_path)
                            st.stop()

                        # Step 3 — Warn if very few pages
                        if len(pages) < 3:
                            st.warning(f"⚠️ Only {len(pages)} page(s) found in Document B.")

                        # Step 4 — Chunk pages
                        chunks = chunk_pages(pages)

                        # Step 5 — Embed and store in ChromaDB (collection: doc_b)
                        embed_and_store(chunks, collection_name="doc_b")

                        # Step 6 — Update session state
                        st.session_state["doc_b_ready"] = True
                        st.session_state["doc_b_name"] = uploaded_file_b.name
                        st.session_state["compare_chat_history"] = []  # reset chat
                        st.session_state["total_pages_b"] = len(pages)
                        st.session_state["total_chunks_b"] = len(chunks)

                    except Exception as e:
                        st.error(f"❌ Error processing Document B: {e}")

                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        if st.session_state["doc_b_ready"]:
            st.success(f"✅ Doc B: {st.session_state['doc_b_name']}")
            col1, col2 = st.columns(2)
            col1.metric("Pages", st.session_state["total_pages_b"])
            col2.metric("Chunks", st.session_state["total_chunks_b"])
            if st.button("🗑️ Clear Doc B", key="clear_b"):
                st.session_state["doc_b_ready"] = False
                st.session_state["doc_b_name"] = ""
                st.session_state["total_pages_b"] = 0
                st.session_state["total_chunks_b"] = 0
                if "pdf_uploader_b" in st.session_state:
                    del st.session_state["pdf_uploader_b"]
                st.rerun()

        if st.session_state["doc_a_ready"] or st.session_state["doc_b_ready"]:
            st.divider()
            if st.button("🗑️ Clear Both & Start Over", key="clear_both"):
                st.session_state["doc_a_ready"] = False
                st.session_state["doc_a_name"] = ""
                st.session_state["total_pages_a"] = 0
                st.session_state["total_chunks_a"] = 0
                st.session_state["doc_b_ready"] = False
                st.session_state["doc_b_name"] = ""
                st.session_state["total_pages_b"] = 0
                st.session_state["total_chunks_b"] = 0
                st.session_state["compare_chat_history"] = []
                if "pdf_uploader_a" in st.session_state:
                    del st.session_state["pdf_uploader_a"]
                if "pdf_uploader_b" in st.session_state:
                    del st.session_state["pdf_uploader_b"]
                st.rerun()

    st.divider()
    st.markdown("**How it works:**")
    st.markdown("1. 📤 Upload a PDF")
    st.markdown("2. 💬 Ask any question")
    st.markdown("3. 📖 Get answer with page numbers")
    st.markdown("4. 🔍 Check the source passages")

# ── Main Chat Area ────────────────────────────────────────
if not compare_mode:
    if st.session_state["pdf_ready"]:

        # Show previous chat history
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

        # ── Question input ────────────────────────────────────
        query = st.chat_input("Ask a question about your document...")

        if query:
            # Show user message immediately
            with st.chat_message("user"):
                st.write(query)

            # Generate and show answer
            with st.chat_message("assistant"):
                with st.spinner("🔍 Searching document..."):
                    try:
                        # Retrieve relevant chunks
                        chunks = hybrid_retrieve(query, top_k=5)

                        # Generate answer with Gemini
                        result = generate_answer(query, chunks)

                        # Display answer
                        st.write(result["answer"])

                        # Display source pages
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
                        st.error(f"❌ Error generating answer: {e}")
                        st.info("💡 Try rephrasing your question or upload a different PDF.")

    else:
        # ── Empty state — no PDF uploaded yet ────────────────
        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 📤 Upload")
            st.markdown("Upload any PDF — textbook, lecture notes, or research paper")

        with col2:
            st.markdown("### 💬 Ask")
            st.markdown("Type any question in plain English")

        with col3:
            st.markdown("### 📖 Cite")
            st.markdown("Get answers with exact page numbers from your document")

        st.divider()

        st.markdown("### 💡 Example Questions You Can Ask")
        st.markdown("""
        - *"What is gradient descent?"*
        - *"Explain the difference between overfitting and underfitting"*
        - *"What are the types of machine learning?"*
        - *"Summarise the key points of chapter 3"*
        - *"What does the author say about neural networks?"*
        """)

        st.info("👈 Upload a PDF from the sidebar to get started!")

else:
    if st.session_state["doc_a_ready"] and st.session_state["doc_b_ready"]:
        # Show previous compare chat history
        for chat in st.session_state["compare_chat_history"]:
            with st.chat_message("user"):
                st.write(chat["question"])
            with st.chat_message("assistant"):
                st.write(chat["answer"])
                col1, col2 = st.columns(2)
                with col1:
                    with st.expander(f"📖 {st.session_state['doc_a_name']} Sources"):
                        for src in chat["doc_a_sources"]:
                            st.markdown(f"**Page {src['page']}**")
                            st.caption(src["snippet"])
                            st.divider()
                with col2:
                    with st.expander(f"📖 {st.session_state['doc_b_name']} Sources"):
                        for src in chat["doc_b_sources"]:
                            st.markdown(f"**Page {src['page']}**")
                            st.caption(src["snippet"])
                            st.divider()

        # ── Comparison Question input ─────────────────────────────
        query = st.chat_input("Ask a question to compare both documents...")

        if query:
            # Show user message immediately
            with st.chat_message("user"):
                st.write(query)

            # Generate and show answer
            with st.chat_message("assistant"):
                with st.spinner("🔍 Comparing documents..."):
                    try:
                        # Call compare_documents
                        result = compare_documents(
                            query,
                            st.session_state["doc_a_name"],
                            st.session_state["doc_b_name"]
                        )

                        # Display answer
                        st.write(result["answer"])

                        # Display source pages
                        col1, col2 = st.columns(2)
                        with col1:
                            with st.expander(f"📖 {st.session_state['doc_a_name']} Sources"):
                                for src in result["doc_a_sources"]:
                                    st.markdown(f"**Page {src['page']}**")
                                    st.caption(src["snippet"])
                                    st.divider()
                        with col2:
                            with st.expander(f"📖 {st.session_state['doc_b_name']} Sources"):
                                for src in result["doc_b_sources"]:
                                    st.markdown(f"**Page {src['page']}**")
                                    st.caption(src["snippet"])
                                    st.divider()

                        # Save to compare chat history
                        st.session_state["compare_chat_history"].append({
                            "question": query,
                            "answer": result["answer"],
                            "doc_a_sources": result["doc_a_sources"],
                            "doc_b_sources": result["doc_b_sources"]
                        })

                    except Exception as e:
                        st.error(f"❌ Error generating comparison: {e}")
                        st.info("💡 Try rephrasing your question or re-uploading documents.")
    else:
        # Empty/Pending state for Compare Mode
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📄 Document A Status")
            if st.session_state["doc_a_ready"]:
                st.success(f"✅ Loaded: {st.session_state['doc_a_name']}")
            else:
                st.info("👈 Please upload Document A in the sidebar")
        with col2:
            st.markdown("### 📄 Document B Status")
            if st.session_state["doc_b_ready"]:
                st.success(f"✅ Loaded: {st.session_state['doc_b_name']}")
            else:
                st.info("👈 Please upload Document B in the sidebar")
        st.divider()
        st.markdown("### 🔀 Document Comparison")
        st.markdown("Once both documents are uploaded, you can ask questions to compare their contents side-by-side.")
        st.markdown("Example questions:")
        st.markdown("""
        - *"What are the different definitions of gradient descent in these textbooks?"*
        - *"Compare the methodologies described in these papers."*
        - *"Summarize the key differences in how the authors approach neural network optimization."*
        """)