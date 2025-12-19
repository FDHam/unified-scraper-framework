# Adapter Development Guide

How to create custom adapters for scraping any web source.

---

## Overview

Adapters are source-specific scrapers that implement a common interface. The framework handles:
- CLI orchestration
- Database operations
- Compression
- Logging
- GitHub Actions integration

You only write the extraction logic.

---

## Step 1: Create Adapter File

Create `adapters/my_source.py`:

```python
"""
MySource Adapter
Scrapes data from mysource.com
"""
from playwright.sync_api import sync_playwright
from typing import List, Dict
from .base import BaseAdapter


class MySourceAdapter(BaseAdapter):
    """Adapter for mysource.com"""

    SOURCE_NAME = "mysource"           # Used in config JSON
    DISPLAY_NAME = "MySource"          # Used in logs

    def validate_url(self, url: str) -> bool:
        """Check if URL belongs to this source."""
        return "mysource.com" in url

    def extract_items(self, url: str, target_config: dict) -> List[Dict]:
        """
        Extract data from the target URL.

        Must return list of dicts with:
            - number: str (identifier)
            - title: str
            - text: str (full content)
            - url: str (source link)
        """
        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(url, wait_until='networkidle')

                # YOUR EXTRACTION LOGIC HERE
                # Example:
                items = page.query_selector_all('.content-item')

                for item in items:
                    results.append({
                        'number': item.get_attribute('data-id'),
                        'title': item.query_selector('.title').inner_text(),
                        'text': item.query_selector('.body').inner_text(),
                        'url': url
                    })

            finally:
                browser.close()

        return results
```

---

## Step 2: Register Adapter

Edit `adapters/__init__.py`:

```python
from .base import BaseAdapter
from .example import ExampleAdapter
from .my_source import MySourceAdapter  # Add import

ADAPTERS = {
    "example": ExampleAdapter,
    "mysource": MySourceAdapter,        # Add registration
}

def get_adapter(source: str) -> BaseAdapter:
    if source not in ADAPTERS:
        raise ValueError(f"Unknown source: {source}. Available: {list(ADAPTERS.keys())}")
    return ADAPTERS[source]()
```

---

## Step 3: Add Configuration

Create or edit `config/my_targets.json`:

```json
{
  "region": "my_region",
  "region_name": "My Region",
  "targets": [
    {
      "id": "target-1",
      "name": "Target One",
      "slug": "target_one",
      "category": "general",
      "url": "https://mysource.com/target-one",
      "metadata": {},
      "source": "mysource",
      "enabled": true
    }
  ]
}
```

---

## Step 4: Run

```bash
# Test your adapter
python main.py target-1 --region my_targets --verbose

# List all targets
python main.py --list --region my_targets
```

---

## Required Interface

Your adapter MUST implement:

| Method | Purpose |
|--------|---------|
| `validate_url(url: str) -> bool` | Return `True` if URL matches your source |
| `extract_items(url: str, config: dict) -> List[Dict]` | Return extracted data |

Each result dict MUST have:

| Key | Type | Description |
|-----|------|-------------|
| `number` | str | Unique identifier within source |
| `title` | str | Item title/heading |
| `text` | str | Full content (will be compressed) |
| `url` | str | Direct link to source |

---

## Playwright Patterns

### Basic Page Load
```python
page.goto(url, wait_until='networkidle')
```

### Wait for Dynamic Content
```python
page.wait_for_selector('.content-loaded', timeout=30000)
```

### Handle Angular/React SPAs
```python
page.goto(url)
page.wait_for_load_state('networkidle')
time.sleep(2)  # Extra buffer for JS rendering
```

### Click and Extract
```python
page.click('.expand-button')
page.wait_for_selector('.expanded-content')
text = page.query_selector('.expanded-content').inner_text()
```

### Navigate Pagination
```python
while True:
    # Extract current page
    items = page.query_selector_all('.item')
    for item in items:
        results.append(extract_item(item))

    # Check for next page
    next_btn = page.query_selector('.next-page:not(.disabled)')
    if not next_btn:
        break
    next_btn.click()
    page.wait_for_load_state('networkidle')
```

### Handle Nested Structures
```python
# First level: sections
sections = page.query_selector_all('.section-link')

for section in sections:
    section_url = section.get_attribute('href')
    page.goto(section_url)

    # Second level: items within section
    items = page.query_selector_all('.item')
    for item in items:
        results.append(extract_item(item))
```

---

## Error Handling

```python
def extract_items(self, url: str, target_config: dict) -> List[Dict]:
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)

            # Check for access denied
            if page.query_selector('.access-denied'):
                self.log_error("Access denied - may need authentication")
                return []

            # Check for empty state
            if page.query_selector('.no-results'):
                self.log_warning("No content found")
                return []

            # Extract...

        except Exception as e:
            self.log_error(f"Extraction failed: {e}")
            return []

        finally:
            browser.close()

    return results
```

---

## Rate Limiting

Add delays to avoid blocking:

```python
import time
import random

def extract_items(self, url: str, target_config: dict) -> List[Dict]:
    results = []

    # ... extraction loop ...

    for item_url in item_urls:
        # Random delay between requests
        time.sleep(random.uniform(1.5, 3.0))

        # Extract item...

    return results
```

---

## Debugging

Enable verbose logging:

```python
def extract_items(self, url: str, target_config: dict) -> List[Dict]:
    self.log_info(f"Starting extraction from {url}")

    # ... extraction ...

    self.log_info(f"Found {len(results)} items")
    self.log_debug(f"First item: {results[0] if results else 'none'}")

    return results
```

Run with `--verbose`:
```bash
python main.py target-1 --verbose
```

---

## Testing Locally

```bash
# Set test database (or use production with caution)
export DATABASE_URL="postgresql://..."

# Run single target
python main.py target-1 --verbose

# Force re-scrape (overwrites existing)
python main.py target-1 --force

# Check logs
cat logs/scrape_target-1_*.log
```

---

## Common Patterns by Site Type

### Static HTML Sites
```python
items = page.query_selector_all('table tr')
for row in items:
    cells = row.query_selector_all('td')
    # Extract from cells...
```

### JavaScript SPAs (React/Angular/Vue)
```python
page.goto(url)
page.wait_for_load_state('networkidle')
page.wait_for_selector('[data-loaded="true"]', timeout=30000)
```

### Sites with Lazy Loading
```python
# Scroll to trigger loading
page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
time.sleep(2)
page.wait_for_selector('.lazy-loaded-content')
```

### Sites Requiring Login
```python
page.goto(login_url)
page.fill('#username', 'user')
page.fill('#password', 'pass')
page.click('#submit')
page.wait_for_url('**/dashboard')
# Now scrape protected content
```

### PDF/Document Links
```python
# Just capture the link, don't download
pdf_link = item.query_selector('a.pdf-download')
pdf_url = pdf_link.get_attribute('href')
results.append({
    'number': 'DOC-1',
    'title': 'Document Title',
    'text': f'[PDF Document: {pdf_url}]',
    'url': pdf_url
})
```

---

## Modifying Core Behavior

### Custom Categorization

Edit `core/categorize.py`:

```python
CATEGORY_KEYWORDS = {
    'your_category': ['keyword1', 'keyword2'],
    # Add more...
}
```

### Custom Database Fields

Edit `core/db.py` and your database schema to add fields.

### Custom Compression

Edit `core/compress.py` to use different algorithms.

---

## Checklist

Before sharing your adapter:

- [ ] `validate_url()` correctly identifies your source
- [ ] `extract_items()` returns proper dict structure
- [ ] Error handling prevents crashes
- [ ] Rate limiting prevents blocking
- [ ] Tested with `--verbose` flag
- [ ] Registered in `adapters/__init__.py`
- [ ] Config JSON created with at least one target
- [ ] Logs show successful extraction

---

## Example: Minimal Adapter

Complete working example:

```python
"""
Example Adapter - Scrapes example.com
"""
from playwright.sync_api import sync_playwright
from typing import List, Dict
import time
from .base import BaseAdapter


class ExampleAdapter(BaseAdapter):
    SOURCE_NAME = "example"
    DISPLAY_NAME = "Example.com"

    def validate_url(self, url: str) -> bool:
        return "example.com" in url

    def extract_items(self, url: str, target_config: dict) -> List[Dict]:
        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                self.log_info(f"Loading {url}")
                page.goto(url, wait_until='networkidle', timeout=60000)

                items = page.query_selector_all('.content-block')
                self.log_info(f"Found {len(items)} items")

                for i, item in enumerate(items):
                    title_el = item.query_selector('h2')
                    body_el = item.query_selector('.body')

                    if title_el and body_el:
                        results.append({
                            'number': f'ITEM-{i+1}',
                            'title': title_el.inner_text().strip(),
                            'text': body_el.inner_text().strip(),
                            'url': url
                        })

                    time.sleep(0.5)  # Small delay

            except Exception as e:
                self.log_error(f"Failed: {e}")

            finally:
                browser.close()

        self.log_info(f"Extracted {len(results)} items")
        return results
```

Register it:

```python
# adapters/__init__.py
from .example import ExampleAdapter

ADAPTERS = {
    "example": ExampleAdapter,
}
```

Run it:

```bash
python main.py my-target --region my_config --verbose
```
