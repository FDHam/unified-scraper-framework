"""LZ4 compression utilities for text storage."""
import lz4.frame
import base64


def compress_text(text: str) -> str:
    """
    Compress text with LZ4 and encode as base64.

    Args:
        text: Original text content

    Returns:
        Base64-encoded compressed string (safe for PostgreSQL storage)
    """
    if not text:
        return ""

    compressed = lz4.frame.compress(text.encode('utf-8'))
    return base64.b64encode(compressed).decode('utf-8')


def decompress_text(compressed: str) -> str:
    """
    Decompress LZ4 compressed text.

    Args:
        compressed: Base64-encoded compressed string

    Returns:
        Original decompressed text
    """
    if not compressed:
        return ""

    decoded = base64.b64decode(compressed.encode('utf-8'))
    decompressed = lz4.frame.decompress(decoded)
    return decompressed.decode('utf-8')
