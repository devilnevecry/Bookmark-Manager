"""Tests for SSRF protection and URL validation."""

from app.services.url_utils import is_allowed_url, normalize_url, extract_domain


def test_allowed_urls():
    """Test that normal HTTP/HTTPS URLs are allowed."""
    assert is_allowed_url("https://example.com") is True
    assert is_allowed_url("http://example.com/page") is True
    assert is_allowed_url("https://sub.domain.example.com/path?query=1") is True


def test_blocked_localhost():
    """Test that localhost is blocked."""
    assert is_allowed_url("http://localhost/") is False
    assert is_allowed_url("https://localhost:8080/") is False
    assert is_allowed_url("http://127.0.0.1/") is False
    assert is_allowed_url("http://[::1]/") is False


def test_blocked_private_ips():
    """Test that private IP ranges are blocked."""
    assert is_allowed_url("http://10.0.0.1/") is False
    assert is_allowed_url("http://172.16.0.1/") is False
    assert is_allowed_url("http://172.31.255.255/") is False
    assert is_allowed_url("http://192.168.1.1/") is False
    assert is_allowed_url("http://169.254.169.254/") is False


def test_blocked_unsupported_schemes():
    """Test that non-HTTP(S) schemes are blocked."""
    assert is_allowed_url("ftp://example.com/") is False
    assert is_allowed_url("file:///etc/passwd") is False
    assert is_allowed_url("javascript:alert(1)") is False
    assert is_allowed_url("gopher://example.com/") is False


def test_extract_domain():
    """Test domain extraction."""
    assert extract_domain("https://example.com/page") == "example.com"
    assert extract_domain("http://sub.example.com/path") == "sub.example.com"
    assert extract_domain("not-a-url") == ""


def test_normalize_url_removes_fragment():
    """Test fragment removal."""
    assert normalize_url("https://example.com/page#section") == "https://example.com/page"


def test_normalize_url_preserves_query():
    """Test that query parameters are preserved."""
    assert normalize_url("https://example.com/page?id=1&foo=bar") == "https://example.com/page?id=1&foo=bar"


def test_normalize_url_lowercase():
    """Test scheme/hostname lowercasing."""
    assert normalize_url("HTTPS://Example.COM/Page") == "https://example.com/Page"