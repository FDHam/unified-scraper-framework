# Scraperdactyl

A modular, adapter-based web scraping framework with Playwright automation, LZ4 compression, PostgreSQL storage, and GitHub Actions integration.

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Real-World Use Cases](#real-world-use-cases)
- [Responsible Scraping](#responsible-scraping)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Creating Custom Adapters](#creating-custom-adapters)
- [AI-Assisted Development](#ai-assisted-development)
- [Configuration Format](#configuration-format)
- [GitHub Actions](#github-actions)
- [Parallel Execution](#parallel-execution)
- [Database Schema](#database-schema)
- [Core Functions](#core-functions)
- [Storage Best Practices](#storage-best-practices)
- [License](#license)

*Important: See [Storage Best Practices](#storage-best-practices)*

---

## Why This Exists

Built to solve a real problem: scraping government data across the entire state of Florida—60+ municipalities, 15,000+ records—from JavaScript-heavy portals with no APIs. The adapter-based architecture handles multiple source formats while GitHub Actions runs 10 targets in parallel.

Now open-sourced for anyone facing similar large-scale data collection challenges.

---

## Real-World Use Cases

- **Government/Legal Data** — Aggregate regulations from scattered municipal sites
- **Price Monitoring** — Track competitor pricing across retail sites daily
- **Research Collection** — Scrape public records from agency portals at scale
- **Real Estate Listings** — Harvest JS-rendered property data across regions
- **Job Market Intel** — Monitor postings across niche industry boards
- **News Monitoring** — Track brand mentions across regional outlets

---

## Responsible Scraping

**Before scraping any source, understand its rules.**

### The Checklist

1. Read the target's **Terms of Service**
2. Check **robots.txt** (`https://example.com/robots.txt`)
3. Look for **API alternatives** (always preferred)
4. Implement **rate limits** based on what you find

### When NOT to Scrape

- TOS explicitly prohibits it
- Data is copyrighted/proprietary
- You'd overload a small server
- An official API exists

<details>
<summary><strong>Rate Limit Implementation Example</strong></summary>

```python
import time
import random

class MyAdapter(BaseAdapter):
    MIN_DELAY = 2.0  # Site allows 1 req/2sec
    MAX_DELAY = 3.0  # Randomize to appear human

    def extract_items(self, url, config):
        for item_url in item_urls:
            time.sleep(random.uniform(self.MIN_DELAY, self.MAX_DELAY))
            # Extract...
```

</details>

<details>
<summary><strong>Rate Limit Quick Reference</strong></summary>

| Site Policy | Delay | max-parallel |
|-------------|-------|--------------|
| No restrictions | 1-2s | 10 |
| Crawl-delay: 5 | 5s+ | 3 |
| API limit 60/min | 1s | 1 |
| TOS prohibits | Don't scrape | 0 |

</details>

---

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt
playwright install chromium

# 2. Configure
export DATABASE_URL="postgresql://user:pass@host:5432/db"

# 3. Run
python main.py --list              # See available targets
python main.py target-1            # Scrape a target
python main.py target-1 --force    # Force re-scrape
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│              (CLI + Orchestration)                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│              Adapter Layer                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │  Example  │  │   Your    │  │  Another  │       │
│  │  Adapter  │  │  Adapter  │  │  Adapter  │       │
│  └───────────┘  └───────────┘  └───────────┘       │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                  Core Layer                         │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  db.py  │  │ compress.py │  │ categorize.py   │ │
│  └─────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│               PostgreSQL Database                   │
└─────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
scraperdactyl/
├── main.py              # CLI entry point
├── requirements.txt     # Dependencies
├── adapters/
│   ├── base.py          # Abstract interface
│   └── example.py       # Template adapter
├── core/
│   ├── db.py            # Database operations
│   ├── compress.py      # LZ4 compression
│   └── categorize.py    # Content classification
├── config/
│   └── example.json     # Target configuration
└── .github/workflows/
    └── scraper.yml      # GitHub Actions
```

---

## Creating Custom Adapters

**Full guide: [ADAPTER_GUIDE.md](ADAPTER_GUIDE.md)**

Quick overview:
1. Copy `adapters/example.py` → `adapters/mysite.py`
2. Implement `validate_url()` and `extract_items()`
3. Register in `adapters/__init__.py`
4. Add targets to `config/` JSON

---

## AI-Assisted Development

Use AI assistants (Claude, ChatGPT, Cursor, Copilot) to accelerate adapter development.

### Key Prompts

**Research rate limits first:**
```
What are the rate limits and robots.txt policies for [target site]?
```

**Create an adapter:**
```
I'm using Scraperdactyl. Here's the base adapter:
[paste adapters/base.py]

Target site structure:
- Items in <div class="listing">
- Titles in <h2>
- Content in <div class="body">

Create an adapter following this pattern.
```

**Debug extraction:**
```
My adapter returns empty. Here's extract_items():
[paste code]

Page HTML:
[paste from browser inspector]
```

### Best Practices

| Do | Don't |
|----|-------|
| Research TOS/rate limits first | Scrape blindly |
| Paste relevant code context | Ask vague questions |
| Test before committing | Copy-paste without review |

---

## Configuration Format

<details>
<summary><strong>Example config/targets.json</strong></summary>

```json
{
  "region": "example",
  "region_name": "Example Region",
  "targets": [
    {
      "id": "target-1",
      "name": "Example Site",
      "slug": "example_site",
      "category": "documentation",
      "url": "https://example.com/docs",
      "metadata": {},
      "source": "example",
      "enabled": true
    }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| id | Yes | Unique CLI identifier |
| name | Yes | Display name |
| url | Yes | Target URL |
| source | Yes | Adapter name |
| enabled | No | Skip if false |

</details>

---

## GitHub Actions

Automated scraping via GitHub Actions:

1. Add `DATABASE_URL` secret to repo settings
2. Actions → Select workflow → "Run workflow"
3. Choose targets (comma-separated or "all")

Workflow: `.github/workflows/scraper.yml`

---

## Parallel Execution

Jobs run with `max-parallel: 10` by default.

<details>
<summary><strong>Safe vs Dangerous Patterns</strong></summary>

```
✅ SAFE: 10 jobs → 10 different pages
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Job 1   │   │ Job 2   │   │ Job 3   │
│Target A │   │Target B │   │Target C │
└────┬────┘   └────┬────┘   └────┬────┘
     ▼             ▼             ▼
  /page-a       /page-b       /page-c

❌ DANGEROUS: 10 jobs → same page = BAN
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Job 1   │   │ Job 2   │   │ Job 3   │
│Target A │   │Target A │   │Target A │
└────┬────┘   └────┬────┘   └────┬────┘
     └─────────────┼─────────────┘
                   ▼
              /page-a (3x load)
```

</details>

<details>
<summary><strong>Configuring Parallel Jobs</strong></summary>

Edit `.github/workflows/scraper.yml`:

```yaml
max-parallel: 3   # Conservative
max-parallel: 10  # Balanced (default)
max-parallel: 20  # Aggressive
```

**Signs of rate limiting:** HTTP 429, 503, captchas, empty responses, timeouts.

**If blocked:** Stop jobs, wait 24-48 hours, reduce parallel count, increase delays.

</details>

---

## Database Schema

<details>
<summary><strong>SQL Schema</strong></summary>

```sql
CREATE TABLE "Source" (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT,
    category TEXT,
    metadata JSONB,
    "sourceUrl" TEXT,
    adapter TEXT,
    "lastScraped" TIMESTAMP
);

CREATE TABLE "Item" (
    id TEXT PRIMARY KEY,
    "sourceId" TEXT REFERENCES "Source"(id),
    number TEXT,
    title TEXT,
    category TEXT,
    summary TEXT,
    tags TEXT[],
    "fullText" TEXT,  -- LZ4 compressed, base64 encoded
    "sourceUrl" TEXT,
    metadata JSONB,
    "scrapedAt" TIMESTAMP,
    UNIQUE("sourceId", number)
);
```

</details>

---

## Core Functions

<details>
<summary><strong>API Reference</strong></summary>

**Database (`core/db.py`)**
```python
source_exists(name) -> bool
get_source_id(name) -> str
insert_source(...) -> str
insert_item(...)
get_item_count(source_id) -> int
```

**Compression (`core/compress.py`)**
```python
compress_text(text) -> str    # LZ4 + base64
decompress_text(data) -> str
```

**Classification (`core/categorize.py`)**
```python
categorize_content(title, text) -> (category, tags)
```

</details>

---

## Storage Best Practices

<details>
<summary><strong>When to Use Compression (Critical)</strong></summary>

LZ4 compression is optimized for **cold storage** — raw scraped data you rarely touch.

**Do NOT** query compressed data directly in production. This creates:
- CPU overhead on every read
- Decompression latency
- Slow full-text search
- Bottlenecks on write-heavy systems

### Recommended Architecture

| Layer | Purpose | Compression | Query Directly? |
|-------|---------|-------------|-----------------|
| Cold | Raw scraped data | LZ4 ✅ | ❌ Never |
| Warm | Derived extracts | Optional | Occasionally |
| Hot | Summaries, structured outputs | None | ✅ Always |

### The Pattern

1. **Scrape** → Store compressed (this framework)
2. **Process** → Decompress once, generate derived outputs
3. **Serve** → Query only uncompressed, structured data

This is how Bloomberg Law, Fastcase, and CourtListener handle large-scale legal data.

</details>

---

## License

MIT — Use freely, modify as needed.

---

## Contributing

1. Fork repo
2. Create adapter or improve core
3. Test locally with `--verbose`
4. Submit PR

See [ADAPTER_GUIDE.md](ADAPTER_GUIDE.md) for detailed adapter development.
