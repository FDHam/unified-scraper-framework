"""PostgreSQL database helpers for scraped data storage.

Generic database layer - customize table names and fields for your use case.
"""
import psycopg2
import psycopg2.extras
import os
import logging
import json

logger = logging.getLogger(__name__)


def get_db_connection():
    """Connect to PostgreSQL database."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)


def source_exists(name: str) -> bool:
    """Check if source already scraped."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM "Source" WHERE name = %s', (name,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def get_source_id(name: str) -> str:
    """Get source ID by name, return None if not found."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id FROM "Source" WHERE name = %s', (name,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None


def insert_source(name: str, slug: str, category: str, metadata: dict,
                  source_url: str, adapter: str = "example") -> str:
    """
    Insert source and return ID.

    Args:
        name: Source display name
        slug: URL-friendly slug
        category: Source category/grouping
        metadata: Additional metadata (JSON)
        source_url: Primary source URL
        adapter: Adapter identifier used for scraping
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO "Source" (id, "createdAt", "updatedAt", name, slug, category, metadata, "sourceUrl", adapter, "lastScraped")
        VALUES (gen_random_uuid(), NOW(), NOW(), %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (name) DO UPDATE SET "lastScraped" = NOW(), "updatedAt" = NOW()
        RETURNING id
    ''', (name, slug, category, psycopg2.extras.Json(metadata), source_url, adapter))
    source_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Source upserted: {name} ({source_id}) [adapter: {adapter}]")
    return source_id


def insert_item(source_id: str, number: str, title: str, category: str,
                summary: str, full_text_compressed: str, tags: list,
                source_url: str, adapter: str = "example"):
    """
    Insert scraped item with LZ4 compressed full text.

    Args:
        source_id: Foreign key to Source
        number: Item identifier/number
        title: Item title
        category: Classified category
        summary: Brief summary (first 200 chars)
        full_text_compressed: LZ4+base64 compressed full text
        tags: List of relevant tags
        source_url: Direct link to item
        adapter: Adapter identifier
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Store adapter in metadata JSON
    metadata = {"adapter": adapter}

    cur.execute('''
        INSERT INTO "Item" (id, "sourceId", number, title, category, summary, tags, "fullText", "sourceUrl", metadata, "scrapedAt")
        VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT ("sourceId", number) DO UPDATE
        SET title = EXCLUDED.title,
            category = EXCLUDED.category,
            summary = EXCLUDED.summary,
            tags = EXCLUDED.tags,
            "fullText" = EXCLUDED."fullText",
            metadata = EXCLUDED.metadata,
            "scrapedAt" = NOW()
    ''', (source_id, number, title, category, summary, tags,
          full_text_compressed, source_url, psycopg2.extras.Json(metadata)))
    conn.commit()
    cur.close()
    conn.close()


def get_item_count(source_id: str) -> int:
    """Get count of items for a source."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM "Item" WHERE "sourceId" = %s', (source_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count
