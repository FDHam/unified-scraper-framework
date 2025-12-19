"""Scraper adapters for different sources."""
from .base import BaseAdapter
from .example import ExampleAdapter

# Register adapters by source name
# ADD YOUR CUSTOM ADAPTERS HERE
ADAPTERS = {
    "example": ExampleAdapter,
    # "mysite": MySiteAdapter,
}


def get_adapter(source: str) -> BaseAdapter:
    """
    Get adapter instance for a given source.

    Args:
        source: Source identifier from config

    Returns:
        Adapter instance

    Raises:
        ValueError: If source not supported
    """
    if source not in ADAPTERS:
        raise ValueError(f"Unknown source: {source}. Available: {list(ADAPTERS.keys())}")
    return ADAPTERS[source]()


__all__ = ['BaseAdapter', 'ExampleAdapter', 'get_adapter', 'ADAPTERS']
