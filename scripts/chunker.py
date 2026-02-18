def chunk_text(text):
    """
    Splits text into chunks based on double newlines and trims whitespace.
    """
    if not text or not text.strip():
        return []

    # Split by double newlines (paragraphs)
    raw_chunks = text.split("\n\n")

    # Filter out empty chunks and trim whitespace
    chunks = [c.strip() for c in raw_chunks if c.strip()]

    return chunks
