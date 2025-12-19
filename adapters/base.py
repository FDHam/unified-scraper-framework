"""Base adapter interface for web scrapers.

All source-specific adapters must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Abstract base class for web scrapers."""

    # Source identifier (override in subclasses)
    SOURCE_NAME: str = "base"

    # Display name for logging
    DISPLAY_NAME: str = "Base Adapter"

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.SOURCE_NAME}")

    @abstractmethod
    def extract_items(self, url: str, target_config: dict) -> List[Dict]:
        """
        Extract items from a target URL.

        Args:
            url: Base URL for the target
            target_config: Target configuration from config JSON

        Returns:
            List of item dicts with keys:
                - number: str (unique identifier)
                - title: str
                - text: str (full content)
                - url: str (direct link)
        """
        pass

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """
        Validate that URL is compatible with this adapter.

        Args:
            url: URL to validate

        Returns:
            True if URL matches this adapter's source
        """
        pass

    def get_source_name(self) -> str:
        """Return the source identifier."""
        return self.SOURCE_NAME

    def log_info(self, message: str):
        """Log info with adapter prefix."""
        self.logger.info(f"[{self.DISPLAY_NAME}] {message}")

    def log_warning(self, message: str):
        """Log warning with adapter prefix."""
        self.logger.warning(f"[{self.DISPLAY_NAME}] {message}")

    def log_error(self, message: str):
        """Log error with adapter prefix."""
        self.logger.error(f"[{self.DISPLAY_NAME}] {message}")

    def log_debug(self, message: str):
        """Log debug with adapter prefix."""
        self.logger.debug(f"[{self.DISPLAY_NAME}] {message}")
