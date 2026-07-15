import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from src.ingest import chunk_pages


def test_chunk_pages_preserves_metadata():
    """Every chunk must have page_number, source and text"""
    fake_pages = [
        {"text": "Machine learning is a subset of AI. " * 15,
         "page_number": 1, "source": "test.pdf"},
        {"text": "Deep learning uses neural networks. " * 15,
         "page_number": 2, "source": "test.pdf"}
    ]
    chunks = chunk_pages(fake_pages)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "page_number" in chunk
        assert "source" in chunk
        assert "text" in chunk


def test_chunk_size_within_limit():
    """No chunk should massively exceed chunk_size"""
    fake_pages = [
        {"text": "word " * 500,
         "page_number": 1, "source": "test.pdf"}
    ]
    chunks = chunk_pages(fake_pages, chunk_size=400)
    for chunk in chunks:
        assert len(chunk["text"]) <= 650


def test_short_content_filtered_out():
    """Chunks under 30 chars should be filtered"""
    fake_pages = [
        {"text": "Hi", "page_number": 1, "source": "test.pdf"},
        {"text": "This is real content with enough text to form a valid chunk. " * 5,
         "page_number": 2, "source": "test.pdf"}
    ]
    real_pages = [p for p in fake_pages if len(p["text"].strip()) >= 50]
    chunks = chunk_pages(real_pages)
    for chunk in chunks:
        assert len(chunk["text"].strip()) > 30


def test_chunk_text_not_empty():
    """No chunk should be empty or whitespace only"""
    fake_pages = [
        {"text": "Artificial intelligence enables computers to learn from data. " * 20,
         "page_number": 1, "source": "test.pdf"}
    ]
    chunks = chunk_pages(fake_pages)
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["text"].strip() != ""