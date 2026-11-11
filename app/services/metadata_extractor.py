"""Metadata extraction service with SSRF protection."""

import httpx
from bs4 import BeautifulSoup
from typing import Optional

from app.services.url_utils import is_allowed_url, extract_domain


MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5 MB
HTTP_TIMEOUT = 15.0
MAX_REDIRECTS = 5

USER_AGENT = "BookmarkManager/1.0 (+https://local/)"  # Identify ourselves


def extract_metadata(url: str) -> dict:
    """Extract metadata from a webpage URL with SSRF protection.

    Returns a dict with keys: title, description, domain, favicon_url, image_url.
    Never raises exceptions that crash the app - returns empty dict on failure.
    """
    if not is_allowed_url(url):
        return {}

    try:
        result = _fetch_and_extract(url)
        return result
    except Exception:
        return {}


def _fetch_and_extract(url: str) -> dict:
    """Fetch page and extract metadata."""
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    with httpx.Client(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
    ) as client:
        response = client.get(url, headers=headers)

        # Check content type
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type.lower():
            return {}

        # Check size
        content = response.content
        if len(content) > MAX_RESPONSE_SIZE:
            content = content[:MAX_RESPONSE_SIZE]

        # Check final URL after redirects for SSRF
        final_url = str(response.url)
        if not is_allowed_url(final_url):
            return {}

        html = content.decode("utf-8", errors="ignore")
        return _parse_html(html, final_url)


def _parse_html(html: str, base_url: str) -> dict:
    """Parse HTML and extract metadata."""
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "title": None,
        "description": None,
        "domain": extract_domain(base_url),
        "favicon_url": None,
        "image_url": None,
    }

    # Extract title with priority: og:title > twitter:title > html title
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        result["title"] = og_title["content"].strip()
    else:
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        if twitter_title and twitter_title.get("content"):
            result["title"] = twitter_title["content"].strip()
        else:
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                result["title"] = title_tag.string.strip()

    # Extract description with priority: og:description > twitter:description > meta description
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        result["description"] = og_desc["content"].strip()
    else:
        twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
        if twitter_desc and twitter_desc.get("content"):
            result["description"] = twitter_desc["content"].strip()
        else:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                result["description"] = meta_desc["content"].strip()

    # Extract Open Graph image
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        result["image_url"] = og_image["content"].strip()

    # Extract favicon
    # Try icon shortcut
    icon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
    if icon and icon.get("href"):
        result["favicon_url"] = _resolve_url(base_url, icon["href"])

    return result


def _resolve_url(base_url: str, href: str) -> str:
    """Resolve a relative URL against a base URL."""
    from urllib.parse import urljoin, urlparse

    resolved = urljoin(base_url, href)
    parsed = urlparse(resolved)
    if parsed.scheme not in ("http", "https"):
        return ""
    return resolved