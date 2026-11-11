"""URL normalization and validation utilities."""

import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def normalize_url(url: str) -> str:
    """Normalize a URL by removing fragments, normalizing scheme/hostname,
    and preserving significant query parameters."""
    if not url:
        return url

    url = url.strip()
    parsed = urlparse(url)

    # Normalize scheme and hostname to lowercase
    scheme = parsed.scheme.lower() or "https"
    hostname = parsed.hostname.lower() if parsed.hostname else ""

    # Remove fragment
    fragment = ""

    # Normalize path
    path = parsed.path or ""
    if not path.startswith("/"):
        path = "/" + path
    # Don't add trailing slash to root
    if path == "":
        path = "/"

    # Preserve query parameters
    query = parsed.query

    normalized = urlunparse((scheme, hostname, path, parsed.params, query, fragment))
    return normalized


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return (parsed.hostname or "").lower()
    except Exception:
        return ""


def is_allowed_url(url: str) -> bool:
    """Check if URL is allowed (HTTP/HTTPS only, no localhost/private/reserved IPs)."""
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return False

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False

        # Block localhost and loopback
        if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False

        # Block private IP ranges
        if hostname.startswith(("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                                 "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                                 "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                                 "172.30.", "172.31.", "192.168.")):
            return False

        # Block link-local addresses
        if hostname.startswith("169.254."):
            return False

        return True
    except Exception:
        return False