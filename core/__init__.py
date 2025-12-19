"""Core utilities for unified scraper framework."""
from .db import (
    get_db_connection,
    source_exists,
    get_source_id,
    insert_source,
    insert_item,
    get_item_count
)
from .categorize import categorize_content
from .compress import compress_text, decompress_text

__all__ = [
    'get_db_connection',
    'source_exists',
    'get_source_id',
    'insert_source',
    'insert_item',
    'get_item_count',
    'categorize_content',
    'compress_text',
    'decompress_text'
]
