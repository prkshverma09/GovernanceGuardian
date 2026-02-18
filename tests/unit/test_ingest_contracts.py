import pytest
import os
from scripts.chunker import chunk_text

@pytest.mark.unit
def test_paragraph_chunking():
    """Verify text is split into chunks by double newlines."""
    text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    chunks = chunk_text(text)
    assert len(chunks) == 3
    assert chunks[0] == "Paragraph 1"
    assert chunks[1] == "Paragraph 2"
    assert chunks[2] == "Paragraph 3"

@pytest.mark.unit
def test_chunking_trims_whitespace():
    """Verify chunks are trimmed of leading/trailing whitespace."""
    text = "  Para 1  \n\n\n  Para 2  "
    chunks = chunk_text(text)
    assert chunks[0] == "Para 1"
    assert chunks[1] == "Para 2"

@pytest.mark.unit
def test_empty_text_returns_empty_list():
    """Verify empty input handles gracefully."""
    assert chunk_text("") == []
    assert chunk_text("   ") == []
