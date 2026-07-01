"""PDF ingestion module."""
import pymupdf  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_pdf(pdf_path: str) -> list:
    """Parse PDF → list of {text, page_number, source}"""
    doc = pymupdf.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        if text.strip():  # skip blank pages
            pages.append({
                "text": text,
                "page_number": page_num + 1,
                "source": pdf_path
            })
    doc.close()
    print(f"✅ Loaded {len(pages)} pages from {pdf_path}")
    return pages

def chunk_pages(pages: list, chunk_size=400, chunk_overlap=50) -> list:
    """Split pages into chunks, keeping page number with each chunk"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = []
    for page in pages:
        splits = splitter.split_text(page["text"])
        for split in splits:
            chunks.append({
                "text": split,
                "page_number": page["page_number"],
                "source": page["source"]
            })
    print(f"✅ Created {len(chunks)} chunks")
    return chunks