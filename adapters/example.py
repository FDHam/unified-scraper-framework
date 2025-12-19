"""
Example Adapter - Template for scraping any website.

Copy this file and customize for your target site.
"""
import time
import random
from typing import List, Dict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from .base import BaseAdapter


class ExampleAdapter(BaseAdapter):
    """Example adapter - customize for your target site."""

    SOURCE_NAME = "example"
    DISPLAY_NAME = "Example.com"

    def validate_url(self, url: str) -> bool:
        """Check if URL matches this adapter's target site."""
        return "example.com" in url

    def extract_items(self, url: str, target_config: dict) -> List[Dict]:
        """
        Extract items from the target URL.

        Customize this method for your specific site structure.
        """
        self.log_info(f"Starting extraction from {url}")
        items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()

            try:
                # Load the page
                self.log_info("Loading page...")
                page.goto(url, wait_until='networkidle', timeout=60000)

                # Wait for content to load (customize selector for your site)
                try:
                    page.wait_for_selector('.content', timeout=10000)
                except PlaywrightTimeout:
                    self.log_warning("Content selector not found, proceeding anyway")

                # Extract items (customize selectors for your site)
                elements = page.query_selector_all('.item, article, .post')
                self.log_info(f"Found {len(elements)} potential items")

                for i, element in enumerate(elements):
                    try:
                        # Extract title
                        title_el = element.query_selector('h1, h2, h3, .title')
                        title = title_el.inner_text().strip() if title_el else f"Item {i+1}"

                        # Extract content
                        content_el = element.query_selector('.content, .body, p')
                        text = content_el.inner_text().strip() if content_el else ""

                        # Extract link
                        link_el = element.query_selector('a')
                        item_url = link_el.get_attribute('href') if link_el else url

                        if text and len(text) > 50:
                            items.append({
                                'number': f'ITEM-{i+1}',
                                'title': title,
                                'text': text,
                                'url': item_url if item_url.startswith('http') else f"{url.rstrip('/')}/{item_url.lstrip('/')}"
                            })
                            self.log_info(f"  Extracted: {title[:50]}...")

                        # Rate limiting
                        time.sleep(random.uniform(0.5, 1.0))

                    except Exception as e:
                        self.log_warning(f"  Failed to extract item {i}: {e}")
                        continue

            except Exception as e:
                self.log_error(f"Extraction failed: {e}")
                import traceback
                self.log_error(traceback.format_exc())

            finally:
                browser.close()

        self.log_info(f"Extracted {len(items)} items total")
        return items
