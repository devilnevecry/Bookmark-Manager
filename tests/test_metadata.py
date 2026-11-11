"""Tests for metadata extraction service."""

from unittest.mock import patch
from app.services.metadata_extractor import extract_metadata


FULL_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>HTML Title</title>
    <meta name="description" content="Meta Description">
    <meta property="og:title" content="OG Title">
    <meta property="og:description" content="OG Description">
    <meta property="og:image" content="https://example.com/image.jpg">
    <link rel="icon" href="https://example.com/favicon.ico">
</head>
<body></body>
</html>"""

MINIMAL_HTML = """<!DOCTYPE html>
<html>
<head><title>Only HTML Title</title></head>
<body></body>
</html>"""

TWITTER_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta name="twitter:title" content="Twitter Title">
    <meta name="twitter:description" content="Twitter Description">
    <meta name="description" content="Meta Description">
</head>
<body></body>
</html>"""


def test_extract_metadata_og_priority():
    """Test that og:title takes priority over HTML title."""
    with patch("app.services.metadata_extractor.httpx.Client") as mock_client:
        mock_response = mock_client.return_value.__enter__.return_value.get.return_value
        mock_response.headers.get.return_value = "text/html"
        mock_response.content = FULL_HTML.encode("utf-8")
        mock_response.url.__str__.return_value = "https://example.com"

        result = extract_metadata("https://example.com")

        assert result["title"] == "OG Title"
        assert result["description"] == "OG Description"
        assert result["image_url"] == "https://example.com/image.jpg"
        assert result["favicon_url"] == "https://example.com/favicon.ico"


def test_extract_metadata_twitter_fallback():
    """Test Twitter card fallback when no OG tags."""
    with patch("app.services.metadata_extractor.httpx.Client") as mock_client:
        mock_response = mock_client.return_value.__enter__.return_value.get.return_value
        mock_response.headers.get.return_value = "text/html"
        mock_response.content = TWITTER_HTML.encode("utf-8")
        mock_response.url.__str__.return_value = "https://example.com"

        result = extract_metadata("https://example.com")

        assert result["title"] == "Twitter Title"
        assert result["description"] == "Twitter Description"


def test_extract_metadata_html_title_fallback():
    """Test HTML title fallback when no OG or Twitter tags."""
    with patch("app.services.metadata_extractor.httpx.Client") as mock_client:
        mock_response = mock_client.return_value.__enter__.return_value.get.return_value
        mock_response.headers.get.return_value = "text/html"
        mock_response.content = MINIMAL_HTML.encode("utf-8")
        mock_response.url.__str__.return_value = "https://example.com"

        result = extract_metadata("https://example.com")

        assert result["title"] == "Only HTML Title"
        assert result["description"] is None


def test_extract_metadata_ssrf_blocked():
    """Test that localhost URLs are blocked."""
    result = extract_metadata("http://localhost:8080/admin")
    assert result == {}

    result = extract_metadata("http://127.0.0.1/")
    assert result == {}

    result = extract_metadata("http://192.168.1.1/")
    assert result == {}

    result = extract_metadata("http://10.0.0.1/")
    assert result == {}


def test_extract_metadata_unsupported_scheme():
    """Test that non-HTTP(S) schemes are blocked."""
    result = extract_metadata("ftp://example.com/file")
    assert result == {}

    result = extract_metadata("file:///etc/passwd")
    assert result == {}

    result = extract_metadata("javascript:alert(1)")
    assert result == {}


def test_extract_metadata_invalid_html():
    """Test handling of invalid/empty HTML."""
    with patch("app.services.metadata_extractor.httpx.Client") as mock_client:
        mock_response = mock_client.return_value.__enter__.return_value.get.return_value
        mock_response.headers.get.return_value = "text/html"
        mock_response.content = b""
        mock_response.url.__str__.return_value = "https://example.com"

        result = extract_metadata("https://example.com")
        assert result == {} or result["title"] is None


def test_extract_metadata_non_html_content_type():
    """Test that non-HTML content types return empty."""
    with patch("app.services.metadata_extractor.httpx.Client") as mock_client:
        mock_response = mock_client.return_value.__enter__.return_value.get.return_value
        mock_response.headers.get.return_value = "application/json"
        mock_response.content = b'{"key": "value"}'
        mock_response.url.__str__.return_value = "https://example.com/api"

        result = extract_metadata("https://example.com/api")
        assert result == {}