#!/usr/bin/env python3
"""
Unified Scraper Framework - Main Entry Point

Modular scraper with adapter-based architecture for any web source.

Usage:
    python main.py <target_id> [--force] [--verbose]

Examples:
    python main.py target-1
    python main.py target-2 --force
    python main.py --list
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from adapters import get_adapter, ADAPTERS
from core import (
    source_exists,
    get_source_id,
    insert_source,
    insert_item,
    get_item_count,
    categorize_content,
    compress_text
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config(region: str = "example") -> dict:
    """Load region configuration file."""
    config_dir = Path(__file__).parent / 'config'
    config_file = config_dir / f'{region}.json'

    if not config_file.exists():
        raise FileNotFoundError(f"Config not found: {config_file}")

    with open(config_file, 'r') as f:
        return json.load(f)


def get_target_config(target_id: str, region: str = "example") -> dict:
    """Get configuration for a specific target."""
    config = load_config(region)

    for target in config['targets']:
        if target['id'] == target_id:
            return target

    raise ValueError(f"Target '{target_id}' not found in {region} config")


def scrape_target(target_id: str, force: bool = False, region: str = "example") -> dict:
    """
    Scrape a single target using the appropriate adapter.

    Args:
        target_id: Target identifier from config
        force: Re-scrape even if already exists
        region: Region config to use (default: example)

    Returns:
        Result dict with status, target name, and item count
    """
    # Load target config
    target = get_target_config(target_id, region)

    target_name = target['name']
    target_slug = target['slug']
    category = target['category']
    metadata = target.get('metadata', {})
    source_url = target['url']
    adapter_name = target.get('source', 'example')

    logger.info("=" * 60)
    logger.info(f"SCRAPING: {target_name}")
    logger.info(f"URL: {source_url}")
    logger.info(f"Adapter: {adapter_name}")
    logger.info("=" * 60)

    # Check if already scraped
    if not force and source_exists(target_name):
        existing_id = get_source_id(target_name)
        existing_count = get_item_count(existing_id)
        logger.info(f"Target already exists with {existing_count} items. Use --force to re-scrape.")
        return {'status': 'skipped', 'target': target_name, 'items': existing_count}

    # Get the appropriate adapter
    try:
        adapter = get_adapter(adapter_name)
        logger.info(f"Using adapter: {adapter.DISPLAY_NAME}")
    except ValueError as e:
        logger.error(f"Adapter error: {e}")
        return {'status': 'error', 'target': target_name, 'error': str(e)}

    # Validate URL
    if not adapter.validate_url(source_url):
        logger.error(f"URL not compatible with {adapter.DISPLAY_NAME} adapter")
        return {'status': 'error', 'target': target_name, 'error': 'URL validation failed'}

    # Extract items
    items = adapter.extract_items(source_url, target)

    if not items:
        logger.warning(f"No items found for {target_name}")
        return {'status': 'empty', 'target': target_name, 'items': 0}

    logger.info(f"Found {len(items)} items")

    # Insert/update source
    source_id = insert_source(
        name=target_name,
        slug=target_slug,
        category=category,
        metadata=metadata,
        source_url=source_url,
        adapter=adapter_name
    )
    logger.info(f"Source ID: {source_id}")

    # Process each item
    success_count = 0
    error_count = 0

    for item in items:
        try:
            # Categorize
            item_category, tags = categorize_content(item['title'], item['text'])

            # Generate summary
            summary = item['text'][:200] + "..." if len(item['text']) > 200 else item['text']

            # Compress full text
            compressed_text = compress_text(item['text'])

            # Insert to database
            insert_item(
                source_id=source_id,
                number=item['number'],
                title=item['title'],
                category=item_category,
                summary=summary,
                full_text_compressed=compressed_text,
                tags=tags,
                source_url=item['url'],
                adapter=adapter_name
            )

            success_count += 1
            logger.info(f"  + {item['number']}: {item['title'][:40]}... [{item_category}]")

        except Exception as e:
            error_count += 1
            logger.error(f"  x Failed: {item.get('number', 'unknown')} - {e}")

    logger.info("")
    logger.info(f"COMPLETE: {target_name}")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info("=" * 60)

    return {
        'status': 'success',
        'target': target_name,
        'items': success_count,
        'errors': error_count,
        'adapter': adapter_name
    }


def list_targets(region: str = "example"):
    """List all configured targets."""
    config = load_config(region)
    print(f"\n{config['region_name']} Targets ({len(config['targets'])} total):\n")

    for target in config['targets']:
        adapter = target.get('source', 'example')
        enabled = "+" if target.get('enabled', True) else "-"
        print(f"  {enabled} {target['id']:<25} [{adapter}] {target['name']}")

    print(f"\nAvailable adapters: {', '.join(ADAPTERS.keys())}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Unified Scraper Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py target-1                 # Scrape target-1
    python main.py target-2 --force         # Force re-scrape
    python main.py --list                   # List all configured targets
    python main.py target-1 -v              # Verbose mode
        """
    )
    parser.add_argument('target', nargs='?', help='Target ID to scrape')
    parser.add_argument('--force', '-f', action='store_true', help='Force re-scrape even if exists')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--list', '-l', action='store_true', help='List all configured targets')
    parser.add_argument('--region', '-r', default='example', help='Region config to use (default: example)')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list:
        list_targets(args.region)
        return

    if not args.target:
        parser.print_help()
        print("\nError: Target ID required (or use --list to see available targets)")
        sys.exit(1)

    # Ensure logs directory exists
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Add file handler for this run
    log_file = logs_dir / f'scrape_{args.target}_{time.strftime("%Y%m%d_%H%M%S")}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)

    try:
        result = scrape_target(args.target, force=args.force, region=args.region)

        # Output summary for GitHub Actions
        print(f"\n::notice::Scraped {result['target']}: {result.get('items', 0)} items [{result.get('adapter', 'unknown')}]")

        if result['status'] == 'success':
            sys.exit(0)
        elif result['status'] == 'skipped':
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"FATAL: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"::error::Scraper failed for {args.target}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
