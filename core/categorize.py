"""Content categorization logic.

Customize CATEGORY_KEYWORDS for your specific use case.
"""

# Category keywords for content classification
# CUSTOMIZE THIS for your scraping domain
CATEGORY_KEYWORDS = {
    "documentation": ["docs", "documentation", "guide", "tutorial", "manual", "reference"],
    "news": ["news", "article", "update", "announcement", "press", "release"],
    "product": ["product", "feature", "pricing", "plan", "subscription", "service"],
    "support": ["help", "support", "faq", "troubleshoot", "issue", "contact"],
    "legal": ["terms", "privacy", "policy", "legal", "agreement", "disclaimer"],
    "general": []  # Default category
}


def categorize_content(title: str, text: str) -> tuple:
    """
    Categorize content and extract relevant tags.

    Args:
        title: Content title
        text: Content full text (first 2000 chars for efficiency)

    Returns:
        (category, relevant_tags)
    """
    combined = (title + " " + text[:2000]).lower()
    tags = []
    best_category = "general"
    max_matches = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == "general":
            continue
        matches = [kw for kw in keywords if kw in combined]
        if matches:
            # Track category with most keyword matches
            if len(matches) > max_matches:
                max_matches = len(matches)
                best_category = category

            # Collect unique tags (limit 3 per category)
            tags.extend(matches[:3])

    return best_category, list(set(tags))
