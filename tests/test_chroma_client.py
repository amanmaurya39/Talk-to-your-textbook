import os
import sys
import importlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import src.embed
import src.retrieve
import src.compare


def test_chroma_client_persistent_locally():
    """Verify that by default (no STREAMLIT_CLOUD env var), client is persistent."""
    # Ensure environment variable is not set
    if "STREAMLIT_CLOUD" in os.environ:
        del os.environ["STREAMLIT_CLOUD"]
        
    # Reload modules to run their module-level client initialization again
    importlib.reload(src.embed)
    importlib.reload(src.retrieve)
    importlib.reload(src.compare)

    assert src.embed.chroma_client._system.settings.is_persistent is True
    assert src.retrieve.chroma_client._system.settings.is_persistent is True
    assert src.compare.chroma_client._system.settings.is_persistent is True


def test_chroma_client_ephemeral_on_cloud():
    """Verify that when STREAMLIT_CLOUD env var is set, client is ephemeral."""
    # Set environment variable
    os.environ["STREAMLIT_CLOUD"] = "true"
    
    try:
        # Reload modules to run their module-level client initialization again
        importlib.reload(src.embed)
        importlib.reload(src.retrieve)
        importlib.reload(src.compare)

        assert src.embed.chroma_client._system.settings.is_persistent is False
        assert src.retrieve.chroma_client._system.settings.is_persistent is False
        assert src.compare.chroma_client._system.settings.is_persistent is False
    finally:
        # Clean up environment variable
        if "STREAMLIT_CLOUD" in os.environ:
            del os.environ["STREAMLIT_CLOUD"]
