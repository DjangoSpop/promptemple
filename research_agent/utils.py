import re
import time
import orjson
import httpx
import math
import bleach
from typing import List, Tuple
from django.conf import settings

# HTML cleaning utilities
TAG_STRIPPER = re.compile(r"(?is)<(script|style).*?>.*?(</\1>)")
TAG_ANY = re.compile(r"(?is)<[^>]+>")


def clean_html_to_text(html: str) -> str:
    """
    Clean HTML content and convert to plain text.

    Args:
        html: Raw HTML content

    Returns:
        Cleaned plain text
    """
    if not html:
        return ""

    # Remove script and style tags with their content
    html = TAG_STRIPPER.sub("", html)

    # Strip remaining HTML tags using bleach
    text = bleach.clean(html, tags=[], strip=True)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def now_ms() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)


def format_json(data: dict) -> str:
    """Format data as JSON using orjson for performance."""
    return orjson.dumps(data, option=orjson.OPT_INDENT_2).decode()


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0-1)
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))

    # Calculate magnitudes
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    # Return cosine similarity
    return dot_product / (magnitude1 * magnitude2)


def extract_domain(url: str) -> str:
    """Extract domain from URL for filtering and categorization."""
    try:
        if url.startswith('http'):
            return url.split('/')[2]
        return url.split('/')[0]
    except (IndexError, AttributeError):
        return ""


def validate_url(url: str) -> bool:
    """Validate if URL is properly formatted and safe to fetch."""
    if not url or not isinstance(url, str):
        return False

    # Basic URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        return False

    # Block localhost and private IPs for security
    blocked_patterns = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '10.',
        '192.168.',
        '172.16.',
        '172.17.',
        '172.18.',
        '172.19.',
        '172.20.',
        '172.21.',
        '172.22.',
        '172.23.',
        '172.24.',
        '172.25.',
        '172.26.',
        '172.27.',
        '172.28.',
        '172.29.',
        '172.30.',
        '172.31.',
    ]

    for pattern in blocked_patterns:
        if pattern in url.lower():
            return False

    return True


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename[:255]  # Limit to filesystem max