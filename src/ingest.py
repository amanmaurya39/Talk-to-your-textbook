import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

# ── Project root path ─────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_pdf(pdf_path: str) -> list:
    """
    Parse a PDF file page by page using PyMuPDF.

    What this does:
    - Opens the PDF
    - Extracts text from each page
    - Stores page number with each page (important for citations later)
    - Skips blank or near-blank pages (less than 50 characters)

    Args:
        pdf_path: Full path to the PDF file

    Returns:
        List of dicts: [{text, page_number, source}, ...]
    """
    # Check file exists before trying to open
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages = []
    skipped = 0

    for page_num in range(len(doc)):
        text = doc[page_num].get_text()

        # Clean up extra whitespace
        text = text.strip()

        # Skip blank or near-blank pages
        # (covers, divider pages, image-only pages)
        if len(text) < 50:
            skipped += 1
            continue

        pages.append({
            "text": text,
            "page_number": page_num + 1,   # 1-indexed (matches PDF page numbers)
            "source": os.path.basename(pdf_path)
        })

    doc.close()

    print(f"✅ Loaded {len(pages)} pages from '{os.path.basename(pdf_path)}'")
    if skipped > 0:
        print(f"   ℹ️  Skipped {skipped} blank/image-only pages")

    return pages


def chunk_pages(pages: list, chunk_size: int = 400, chunk_overlap: int = 50) -> list:
    """
    Split pages into smaller chunks for embedding and retrieval.

    Why chunking?
    - Embedding models have token limits
    - Smaller chunks = more precise retrieval
    - Overlap ensures answers spanning two chunks aren't lost

    chunk_size=400:  Not too small (loses context), not too large (loses precision)
    chunk_overlap=50: Each chunk shares 50 chars with the next — prevents cut-off answers

    Separators order (tries these in order, falls back to next if needed):
    1. Double newline  → paragraph boundary (best split point)
    2. Single newline  → line boundary
    3. Period/!/? → sentence boundary
    4. Space           → word boundary (last resort)

    Args:
        pages: Output from load_pdf()
        chunk_size: Max characters per chunk (default 400)
        chunk_overlap: Characters shared between adjacent chunks (default 50)

    Returns:
        List of dicts: [{text, page_number, source}, ...]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", "!", "?", " ", ""]
    )

    chunks = []
    for page in pages:
        splits = splitter.split_text(page["text"])

        for split in splits:
            # Only keep chunks with meaningful content
            # Filters out chunks that are just whitespace or very short
            if len(split.strip()) > 30:
                chunks.append({
                    "text": split.strip(),
                    "page_number": page["page_number"],
                    "source": page["source"]
                })

    # Print stats for debugging
    if chunks:
        avg_len = sum(len(c["text"]) for c in chunks) // len(chunks)
        print(f"✅ Created {len(chunks)} chunks")
        print(f"   ℹ️  Average chunk size: {avg_len} characters")
        print(f"   ℹ️  Chunk size setting: {chunk_size} | Overlap: {chunk_overlap}")
    else:
        print("⚠️  No chunks created — PDF may have no extractable text")

    return chunks


def get_pdf_info(pdf_path: str) -> dict:
    """
    Get basic metadata about a PDF without fully parsing it.
    Used to show document info in the Streamlit sidebar.

    Args:
        pdf_path: Full path to the PDF file

    Returns:
        dict with: total_pages, title, author, file_size_mb
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    doc = fitz.open(pdf_path)

    info = {
        "total_pages": len(doc),
        "title": doc.metadata.get("title", "Unknown") or "Unknown",
        "author": doc.metadata.get("author", "Unknown") or "Unknown",
        "file_size_mb": round(os.path.getsize(pdf_path) / (1024 * 1024), 2)
    }

    doc.close()
    return info


def validate_pdf(pdf_path: str) -> dict:
    """
    Check if a PDF is suitable for RAG before processing.
    Returns a validation result with warnings if needed.

    Checks:
    - File exists
    - Is actually a PDF
    - Has extractable text (not scanned)
    - Has enough content (more than 1 page)

    Args:
        pdf_path: Full path to the PDF file

    Returns:
        dict: {valid: bool, warnings: list, errors: list}
    """
    result = {
        "valid": True,
        "warnings": [],
        "errors": []
    }

    # Check 1 — File exists
    if not os.path.exists(pdf_path):
        result["valid"] = False
        result["errors"].append(f"File not found: {pdf_path}")
        return result

    # Check 2 — Try to open as PDF
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Cannot open file as PDF: {e}")
        return result

    # Check 3 — Has pages
    if len(doc) == 0:
        result["valid"] = False
        result["errors"].append("PDF has no pages")
        doc.close()
        return result

    # Check 4 — Has extractable text
    total_text = ""
    for page in doc:
        total_text += page.get_text()

    if len(total_text.strip()) < 100:
        result["valid"] = False
        result["errors"].append(
            "PDF has no extractable text. "
            "It may be a scanned image. "
            "Please use a text-based PDF."
        )
        doc.close()
        return result

    # Check 5 — Warn if very short
    if len(doc) < 3:
        result["warnings"].append(
            f"PDF only has {len(doc)} page(s). "
            "Answers may be limited. A longer document works better."
        )

    # Check 6 — Warn if very large
    file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    if file_size_mb > 20:
        result["warnings"].append(
            f"Large file ({file_size_mb:.1f}MB). "
            "Processing may take 2-3 minutes."
        )

    doc.close()
    return result