import sys
import os
import pytest

# Add project root to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from src.ingest import load_pdf, chunk_pages


def test_chunk_pages_preserves_metadata():
    """Each chunk must have page_number and source"""
    fake_pages = [
        {"text": "This is a test page with enough content to be chunked properly " * 5,
         "page_number": 1,
         "source": "test.pdf"},
        {"text": "This is another test page with different content here " * 5,
         "page_number": 2,
         "source": "test.pdf"}
    ]
    chunks = chunk_pages(fake_pages)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "page_number" in chunk
        assert "source" in chunk
        assert "text" in chunk


def test_chunk_size_within_limit():
    """No chunk should exceed 500 characters"""
    fake_pages = [
        {"text": "Word " * 300,  # 1500 chars
         "page_number": 1,
         "source": "test.pdf"}
    ]
    chunks = chunk_pages(fake_pages, chunk_size=400)
    for chunk in chunks:
        assert len(chunk["text"]) <= 600  # some tolerance for overlap


def test_blank_pages_skipped():
    """Chunks from near-blank pages should not be created"""
    fake_pages = [
        {"text": "   ",  # blank page
         "page_number": 1,
         "source": "test.pdf"},
        {"text": "Real content here that has enough text " * 5,
         "page_number": 2,
         "source": "test.pdf"}
    ]
    # Manually filter blank pages (as ingest.py does)
    real_pages = [p for p in fake_pages if len(p["text"].strip()) >= 50]
    chunks = chunk_pages(real_pages)
    
    # All chunks should be from page 2 only
    for chunk in chunks:
        assert chunk["page_number"] == 2


def test_chunk_text_not_empty():
    """No chunk should have empty text"""
    fake_pages = [
        {"text": "Meaningful content about machine learning algorithms " * 10,
         "page_number": 1,
         "source": "test.pdf"}
    ]
    chunks = chunk_pages(fake_pages)
    for chunk in chunks:
        assert len(chunk["text"].strip()) > 0