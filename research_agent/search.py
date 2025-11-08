"""
Web search and URL fetching functionality for research agent.
"""
import logging
import asyncio
from typing import List, Dict, Tuple, Optional
from django.conf import settings
from .utils import validate_url, extract_domain

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


def web_search(query: str, k: int = 6) -> List[Dict[str, str]]:
    """
    Perform web search using configured search provider.

    Args:
        query: Search query
        k: Number of results to return

    Returns:
        List of search results with 'url' and 'title' keys
    """
    search_provider = getattr(settings, 'RESEARCH', {}).get('SEARCH_PROVIDER', 'tavily')

    if search_provider == 'tavily':
        return _tavily_search(query, k)
    elif search_provider == 'serpapi':
        return _serpapi_search(query, k)
    else:
        logger.warning(f"Unknown search provider: {search_provider}")
        return []


def _tavily_search(query: str, k: int) -> List[Dict[str, str]]:
    """
    Search using Tavily API.

    Args:
        query: Search query
        k: Number of results

    Returns:
        List of search results
    """
    try:
        from tavily import TavilyClient

        api_key = getattr(settings, 'TAVILY_API_KEY', '')
        if not api_key:
            logger.error("TAVILY_API_KEY not configured")
            return []

        client = TavilyClient(api_key=api_key)

        response = client.search(
            query=query,
            max_results=k,
            include_answer=False,
            include_raw_content=False
        )

        results = []
        for result in response.get("results", [])[:k]:
            url = result.get("url", "")
            title = result.get("title", "") or url

            # Validate URL before adding
            if validate_url(url):
                results.append({
                    "url": url,
                    "title": title
                })

        logger.info(f"Tavily search returned {len(results)} results for: {query}")
        return results

    except ImportError:
        logger.error("tavily-python not installed. Install with: pip install tavily-python")
        return []
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return []


def _serpapi_search(query: str, k: int) -> List[Dict[str, str]]:
    """
    Search using SerpAPI (Google Search).

    Args:
        query: Search query
        k: Number of results

    Returns:
        List of search results
    """
    try:
        import serpapi

        api_key = getattr(settings, 'SERPAPI_API_KEY', '')
        if not api_key:
            logger.error("SERPAPI_API_KEY not configured")
            return []

        client = serpapi.GoogleSearch({
            "q": query,
            "api_key": api_key,
            "num": k,
            "hl": "en",
            "gl": "us"
        })

        response = client.get_dict()

        results = []
        for result in response.get("organic_results", [])[:k]:
            url = result.get("link", "")
            title = result.get("title", "") or url

            # Validate URL before adding
            if validate_url(url):
                results.append({
                    "url": url,
                    "title": title
                })

        logger.info(f"SerpAPI search returned {len(results)} results for: {query}")
        return results

    except ImportError:
        logger.error("google-search-results not installed. Install with: pip install google-search-results")
        return []
    except Exception as e:
        logger.error(f"SerpAPI search error: {e}")
        return []


async def fetch_url(client, url: str, timeout: int = 15) -> Tuple[int, str]:
    """
    Fetch content from a single URL asynchronously.

    Args:
        client: httpx.AsyncClient instance
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Tuple of (status_code, content)
    """
    try:
        # Validate URL before fetching
        if not validate_url(url):
            logger.warning(f"Invalid URL blocked: {url}")
            return 403, ""

        response = await client.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "PromptTempleBot/1.0 (+https://prompt-temple.com/bot)"
            }
        )

        # Check content type
        content_type = response.headers.get("content-type", "").lower()
        if not any(ct in content_type for ct in ["text/html", "text/plain", "application/xhtml"]):
            logger.warning(f"Skipping non-text content: {content_type} from {url}")
            return response.status_code, ""

        return response.status_code, response.text

    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching URL: {url}")
        return 408, ""
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return 0, ""


async def fetch_urls_batch(urls: List[str], timeout: int = 15, max_concurrent: int = 5) -> List[Tuple[str, int, str]]:
    """
    Fetch multiple URLs concurrently with rate limiting.

    Args:
        urls: List of URLs to fetch
        timeout: Request timeout in seconds
        max_concurrent: Maximum concurrent requests

    Returns:
        List of tuples: (url, status_code, content)
    """
    if not urls:
        return []
    
    if not httpx:
        logger.error("httpx not available for URL fetching. Install with: pip install httpx")
        return [(url, 0, "") for url in urls]

    results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_semaphore(client, url):
        async with semaphore:
            status, content = await fetch_url(client, url, timeout)
            return url, status, content

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            limits=httpx.Limits(max_connections=max_concurrent),
            timeout=httpx.Timeout(timeout)
        ) as client:
            tasks = [fetch_with_semaphore(client, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Fetch error: {result}")
                else:
                    valid_results.append(result)

            return valid_results

    except Exception as e:
        logger.error(f"Batch fetch error: {e}")
        return []


def search_and_rank_urls(query: str, k: int = 6) -> List[Dict[str, str]]:
    """
    Search for URLs and optionally rank them by relevance.

    Args:
        query: Search query
        k: Number of URLs to return

    Returns:
        List of ranked search results
    """
    results = web_search(query, k * 2)  # Get more results for ranking

    if not results:
        return []

    # For now, just return the first k results
    # TODO: Implement relevance ranking based on domain authority, content freshness, etc.
    return results[:k]


def filter_duplicate_domains(results: List[Dict[str, str]], max_per_domain: int = 2) -> List[Dict[str, str]]:
    """
    Filter results to avoid too many from the same domain.

    Args:
        results: List of search results
        max_per_domain: Maximum results per domain

    Returns:
        Filtered results
    """
    domain_counts = {}
    filtered = []

    for result in results:
        domain = extract_domain(result.get("url", ""))
        if not domain:
            continue

        count = domain_counts.get(domain, 0)
        if count < max_per_domain:
            filtered.append(result)
            domain_counts[domain] = count + 1

    return filtered


def get_robots_txt(domain: str) -> Optional[str]:
    """
    Fetch robots.txt for a domain (for respectful crawling).

    Args:
        domain: Domain to check

    Returns:
        robots.txt content or None
    """
    try:
        import httpx

        robots_url = f"https://{domain}/robots.txt"

        with httpx.Client(timeout=5) as client:
            response = client.get(robots_url)
            if response.status_code == 200:
                return response.text
    except Exception as e:
        logger.debug(f"Could not fetch robots.txt for {domain}: {e}")

    return None


def is_crawl_allowed(url: str, user_agent: str = "PromptTempleBot") -> bool:
    """
    Check if crawling is allowed for URL (basic robots.txt check).

    Args:
        url: URL to check
        user_agent: User agent string

    Returns:
        True if crawling is likely allowed
    """
    domain = extract_domain(url)
    if not domain:
        return False

    # For now, assume crawling is allowed
    # TODO: Implement proper robots.txt parsing
    return True