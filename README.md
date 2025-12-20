# Unified Scraper Framework

A modular, adapter-based web scraping framework with LZ4 compression and PostgreSQL storage.

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Real-World Use Cases](#real-world-use-cases)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Creating Custom Adapters](#creating-custom-adapters)
- [GitHub Actions](#github-actions)
- [Parallel Execution & Rate Limiting](#parallel-execution--rate-limiting)
- [Configuration Format](#configuration-format)
- [Database Schema](#database-schema)
- [Core Functions](#core-functions)
- [Compression Details](#compression-details)
- [Rate Limiting](#rate-limiting)
- [Responsible Scraping: Rate Limits & TOS](#responsible-scraping-rate-limits--tos)
- [AI-Assisted Development](#ai-assisted-development)
- [License](#license)
- [Contributing](#contributing)

---

## Why This Exists

This framework was born from a real problem: building a legal rights platform that needed municipal ordinance data across the entire state of Florida. Each city's legal code lived on different platforms (Municode, American Legal, etc.) with different page structures.

Manual copying wasn't feasible. Existing scraping tools couldn't handle JavaScript-heavy legal portals. So I built an adapter-based system that could scrape any source with a single config change—and run 10 cities in parallel via GitHub Actions.

**The result**: Successfully scraped the state of Florida—60+ municipalities, 15,000+ ordinances, all stored and searchable in a production web app. The framework is source-agnostic, so I'm sharing it for others facing similar large-scale data collection challenges.

---

## Real-World Use Cases

**1. Legal/Government Data Aggregation**
- **Problem**: Building a compliance app but regulations are scattered across 50 municipal websites with no API.
- **Solution**: One adapter per site structure, parallel scraping via GitHub Actions, centralized database.

**2. Competitive Price Monitoring**
- **Problem**: E-commerce team needs daily competitor pricing from 20 retail sites.
- **Solution**: Adapters for each retailer, scheduled GitHub Actions runs, price history in PostgreSQL for trend analysis.

**3. Research Data Collection**
- **Problem**: Academic study requires scraping 10,000 public records from state agency portals.
- **Solution**: Robust error handling, LZ4 compression for large text fields, resume-on-failure with `--force` flag.

**4. Real Estate Listings Aggregation**
- **Problem**: Property investment tool needs listings from multiple MLS-adjacent sites.
- **Solution**: Playwright handles JavaScript-rendered listings, parallel jobs scrape different regions simultaneously.

**5. Job Market Intelligence**
- **Problem**: Recruiting firm wants to track job postings across niche industry boards.
- **Solution**: Adapters extract title/company/requirements, categorization tags enable filtering, daily scheduled scrapes.

**6. News & Media Monitoring**
- **Problem**: PR team needs to track brand mentions across regional news sites.
- **Solution**: Adapters for each outlet, keyword-based categorization, compressed full-text storage for search.

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
│  │  Example  │  │  Custom   │  │   Your    │       │
│  │  Adapter  │  │  Adapter  │  │  Adapter  │       │
│  └───────────┘  └───────────┘  └───────────┘       │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│                  Core Layer                         │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  db.py  │  │ compress.py │  │ categorize.py   │ │
│  │ (CRUD)  │  │   (LZ4)     │  │ (Classification)│ │
│  └─────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│               PostgreSQL Database                   │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Set Database URL

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

### 3. Run Scraper

```bash
# List available targets
python main.py --list

# Scrape a specific target
python main.py target-1

# Force re-scrape
python main.py target-1 --force

# Verbose output
python main.py target-1 --verbose
```

---

## Directory Structure

```
unified-scraper-framework/
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── adapters/
│   ├── __init__.py        # Adapter registry
│   ├── base.py            # Abstract base class
│   └── example.py         # Example adapter (template)
├── core/
│   ├── __init__.py        # Core exports
│   ├── db.py              # Database operations
│   ├── compress.py        # LZ4 compression
│   └── categorize.py      # Content classification
├── config/
│   └── example.json       # Target configuration
├── .github/workflows/
│   └── scraper.yml        # GitHub Actions workflow
└── logs/                  # Runtime logs (gitignored)
```

---

## Creating Custom Adapters

**See [ADAPTER_GUIDE.md](ADAPTER_GUIDE.md) for complete instructions.**

Quick overview:

1. Copy `adapters/example.py` to `adapters/mysite.py`
2. Customize `validate_url()` and `extract_items()`
3. Register in `adapters/__init__.py`
4. Add targets to config JSON

---

## GitHub Actions

Automated scraping via GitHub Actions:

1. Add `DATABASE_URL` secret to repo settings
2. Go to Actions → Select workflow → "Run workflow"
3. Choose targets (single, multiple, or "all")

**Workflow location**: `.github/workflows/scraper.yml`

---

## Parallel Execution & Rate Limiting

**CRITICAL: Understand this before running jobs.**

### How Jobs Run

The workflow uses a **matrix strategy** with `max-parallel: 10`:

```yaml
strategy:
  matrix:
    target: [target-1, target-2, ...]
  max-parallel: 10
```

This means:
- Up to 10 **different targets** can run simultaneously
- Each target runs in its own isolated container
- All 10 jobs hit **different pages** on the target site

### What's Safe vs. Dangerous

| Scenario | Safe? | Why |
|----------|-------|-----|
| 10 jobs → 10 different target pages | Yes | Different URLs, distributed load |
| 10 jobs → same target page | No | Hammers one URL, triggers rate limits |
| 1 job scraping multiple pages sequentially | Yes | Built-in delays between requests |

### Visual Example

```
SAFE: Parallel jobs hitting different targets
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Job 1   │   │ Job 2   │   │ Job 3   │
│Target A │   │Target B │   │Target C │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     ▼             ▼             ▼
  /page-a       /page-b       /page-c
     │             │             │
     └─────────────┴─────────────┘
              Target Site
         (3 different pages)

DANGEROUS: Multiple jobs hitting same target
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Job 1   │   │ Job 2   │   │ Job 3   │
│Target A │   │Target A │   │Target A │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     └─────────────┼─────────────┘
                   ▼
              /page-a
                   │
              Target Site
         (1 page, 3x load = BAN)
```

### Rate Limit Guidelines

| Target Site Type | Recommended Delay | Max Parallel |
|------------------|-------------------|--------------|
| Government sites | 3-5 seconds | 5 |
| High-traffic sites | 1-2 seconds | 15 |
| Unknown sites | 5+ seconds | 3 |

### Configuring Parallel Jobs

Edit `.github/workflows/scraper.yml`:

```yaml
# Conservative (safer for strict sites)
max-parallel: 3

# Balanced (default)
max-parallel: 10

# Aggressive (only for permissive sites)
max-parallel: 20
```

### Signs You're Being Rate Limited

- HTTP 429 (Too Many Requests)
- HTTP 503 (Service Unavailable)
- Captcha challenges appearing
- Empty responses after initial success
- Connection timeouts increasing

### If You Get Blocked

1. Stop all jobs immediately
2. Wait 24-48 hours before retrying
3. Reduce `max-parallel` setting
4. Increase delays in adapter code
5. Consider adding proxy rotation (advanced)

---

## Configuration Format

`config/<region>.json`:

```json
{
  "region": "example",
  "region_name": "Example Region",
  "targets": [
    {
      "id": "target-1",
      "name": "Example Site 1",
      "slug": "example_site_1",
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
| `id` | Yes | Unique identifier (CLI argument) |
| `name` | Yes | Display name |
| `slug` | Yes | URL-safe identifier |
| `category` | Yes | Target category |
| `url` | Yes | Target URL |
| `metadata` | No | Additional JSON metadata |
| `source` | Yes | Adapter name |
| `enabled` | No | Skip if `false` |

---

## Database Schema

```sql
-- Source table
CREATE TABLE "Source" (
    id TEXT PRIMARY KEY,
    "createdAt" TIMESTAMP DEFAULT NOW(),
    "updatedAt" TIMESTAMP DEFAULT NOW(),
    name TEXT NOT NULL UNIQUE,
    slug TEXT,
    category TEXT,
    metadata JSONB,
    "sourceUrl" TEXT,
    adapter TEXT,
    "lastScraped" TIMESTAMP
);

-- Item table
CREATE TABLE "Item" (
    id TEXT PRIMARY KEY,
    "sourceId" TEXT REFERENCES "Source"(id),
    number TEXT,
    title TEXT,
    category TEXT,
    summary TEXT,
    tags TEXT[],
    "fullText" TEXT,           -- LZ4 compressed, base64 encoded
    "sourceUrl" TEXT,
    metadata JSONB,
    "scrapedAt" TIMESTAMP DEFAULT NOW(),
    UNIQUE("sourceId", number)
);
```

---

## Core Functions

### Database (`core/db.py`)

```python
source_exists(name: str) -> bool
get_source_id(name: str) -> str
insert_source(...) -> str
insert_item(...)
get_item_count(source_id: str) -> int
```

### Compression (`core/compress.py`)

```python
compress_text(text: str) -> str      # Returns base64-encoded LZ4
decompress_text(data: str) -> str    # Reverses compression
```

### Classification (`core/categorize.py`)

```python
categorize_content(title: str, text: str) -> tuple[str, list[str]]
# Returns (category, tags)
```

---

## Compression Details

- **Algorithm**: LZ4 (fast compression/decompression)
- **Encoding**: Base64 for database storage
- **Ratio**: 3-6x reduction on text content
- **Location**: Compression happens in `core/compress.py`

---

## Rate Limiting

Built-in delays prevent blocking:

- **Between pages**: 0.5-1 seconds (configurable in adapter)
- **Between targets**: 2 seconds
- **On error**: Exponential backoff

Adjust in adapter implementations.

---

## Responsible Scraping: Rate Limits & TOS

**Before scraping any source, you must understand its rules.**

### Check Terms of Service

Every website has terms governing automated access. Before building an adapter:

1. Read the target site's Terms of Service
2. Check for a `robots.txt` file (`https://example.com/robots.txt`)
3. Look for API alternatives (APIs are always preferred over scraping)
4. Respect `Disallow` directives in robots.txt

### Research Rate Limits

Use your AI assistant to research rate limits:

**Prompt:**
```
What are the rate limits and scraping policies for [target site]?
Check their:
- Terms of Service
- robots.txt directives
- API documentation (if available)
- Any public statements on automated access
```

### Implement Rate Limits in Your Adapter

Once you know the limits, implement them:

```python
import time
import random

class MyAdapter(BaseAdapter):
    # Site allows 1 request per 2 seconds
    MIN_DELAY = 2.0
    MAX_DELAY = 3.0  # Add randomization to appear more human

    def extract_items(self, url: str, target_config: dict) -> List[Dict]:
        results = []

        for item_url in item_urls:
            # Respectful delay based on site's rate limits
            time.sleep(random.uniform(self.MIN_DELAY, self.MAX_DELAY))

            # Extract item...

        return results
```

### Rate Limit Quick Reference

| Site Policy | Recommended Delay | max-parallel |
|-------------|-------------------|--------------|
| No robots.txt restrictions | 1-2 seconds | 10 |
| "Crawl-delay: 5" in robots.txt | 5+ seconds | 3 |
| API rate limit: 60/min | 1 second | 1 |
| Strict TOS against scraping | Don't scrape | 0 |

### When NOT to Scrape

- TOS explicitly prohibits scraping
- Site requires authentication you don't have rights to
- Data is copyrighted/proprietary
- You'd be overloading a small server
- An official API exists

**Bottom line**: Research first, configure delays accordingly, and scrape responsibly.

---

## AI-Assisted Development

Modern AI assistants (Claude, ChatGPT, Cursor, GitHub Copilot, etc.) can accelerate your adapter development when used methodically.

### Effective Prompts

**Creating a new adapter:**
```
I'm using the Unified Scraper Framework. Here's the base adapter interface:
[paste adapters/base.py]

I need to scrape [target site]. The page structure is:
- Items are in <div class="listing">
- Titles are in <h2>
- Content is in <div class="body">

Create an adapter following the existing pattern.
```

**Researching rate limits:**
```
What are the rate limits and robots.txt policies for [target site]?
How should I configure delays in my scraper to comply?
```

**Debugging extraction issues:**
```
My adapter returns empty results. Here's my extract_items() method:
[paste your code]

The page HTML structure is:
[paste relevant HTML from browser inspector]

Why isn't it finding elements?
```

**Modifying the database schema:**
```
I need to add a "price" field to store numeric values. Here's the current db.py:
[paste core/db.py]

How do I add this field and update insert_item()?
```

### Best Practices

| Do | Don't |
|----|-------|
| Paste relevant code context | Ask vague questions without code |
| Research TOS/rate limits first | Scrape blindly and get blocked |
| Describe the specific site structure | Expect AI to guess your target |
| Test AI suggestions before committing | Blindly copy-paste without review |
| Iterate on prompts if results are off | Give up after one attempt |

### Recommended Workflow

1. **Research the target** - Use AI to check TOS, robots.txt, rate limits
2. **Configure delays** - Implement appropriate rate limiting in your adapter
3. **Describe your target** - Share the URL structure and what you're extracting
4. **Provide the base code** - Paste `base.py` and `example.py` as reference
5. **Ask for specific changes** - "Add pagination support" is better than "make it work"
6. **Review and test** - Run with `--verbose`, verify output before database writes
7. **Iterate** - Refine based on actual results

### Example: Building a Job Board Adapter

**Step 1 - Research:**
```
What are the scraping policies for jobs.example.com?
Check their robots.txt and TOS.
```

**Step 2 - Build:**
```
Create an adapter for jobs.example.com with:
- Job title in <h3 class="job-title">
- Company in <span class="company">
- Description in <div class="description">

Include a 3-second delay between requests per their robots.txt Crawl-delay.
Follow the BaseAdapter pattern.
```

AI generates working code. You verify TOS compliance, test thoroughly, and handle edge cases.

---

## License

MIT - Use freely, modify as needed.

---

## Contributing

1. Fork repo
2. Create adapter or improve core
3. Test locally
4. Submit PR

See [ADAPTER_GUIDE.md](ADAPTER_GUIDE.md) for adapter development.
