"""Tests for import/export functionality."""

import pytest
from app.services import import_export as ie
from app.schemas import ImportResult


def test_parse_netscape_html():
    """Test parsing Netscape Bookmark HTML."""
    html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
    <DT><H3>Development</H3>
    <DL><p>
        <DT><A HREF="https://github.com" ADD_DATE="1234567890">GitHub</A>
    </DL><p>
    <DT><A HREF="https://example.com" ADD_DATE="1234567891">Example</A>
</DL><p>"""

    parsed = ie.parse_netscape_html(html)

    assert len(parsed["bookmarks"]) == 2
    assert parsed["bookmarks"][0]["url"] == "https://github.com"
    assert parsed["bookmarks"][0]["title"] == "GitHub"
    assert parsed["bookmarks"][0]["folder"] == "Development"
    assert parsed["bookmarks"][1]["url"] == "https://example.com"
    assert parsed["bookmarks"][1]["folder"] is None
    assert "Development" in parsed["folders"]


def test_import_netscape_html(db_session):
    """Test importing bookmarks from Netscape HTML."""
    html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
    <DT><H3>Development</H3>
    <DL><p>
        <DT><A HREF="https://github.com" ADD_DATE="1234567890">GitHub</A>
        <DT><A HREF="https://python.org" ADD_DATE="1234567891">Python</A>
    </DL><p>
    <DT><A HREF="https://example.com" ADD_DATE="1234567892">Example</A>
</DL><p>"""

    result = ie.import_netscape_html(db_session, html)

    assert result.imported == 3
    assert result.skipped == 0

    # Check that category was created
    from app.services.bookmark_service import get_categories
    categories = get_categories(db_session)
    assert len(categories) == 1
    assert categories[0].name == "Development"


def test_import_duplicate_urls(db_session):
    """Test that duplicate URLs are skipped during import."""
    from app.services.bookmark_service import create_bookmark
    from app.schemas import BookmarkCreate

    # Pre-create a bookmark
    create_bookmark(db_session, BookmarkCreate(url="https://github.com", title="GitHub"), fetch_metadata=False)

    html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
    <DT><A HREF="https://github.com" ADD_DATE="1234567890">GitHub</A>
</DL><p>"""

    result = ie.import_netscape_html(db_session, html)

    assert result.imported == 0
    assert result.skipped == 1


def test_import_invalid_urls(db_session):
    """Test that invalid URLs are skipped."""
    html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
    <DT><A HREF="not-a-url" ADD_DATE="1234567890">Invalid</A>
    <DT><A HREF="ftp://files.com" ADD_DATE="1234567891">FTP</A>
    <DT><A HREF="https://valid.com" ADD_DATE="1234567892">Valid</A>
</DL><p>"""

    result = ie.import_netscape_html(db_session, html)

    assert result.imported == 1
    assert result.skipped == 2


def test_export_bookmarks_to_netscape(db_session):
    """Test exporting bookmarks to Netscape HTML."""
    from app.services.bookmark_service import create_bookmark
    from app.schemas import BookmarkCreate

    create_bookmark(db_session, BookmarkCreate(url="https://github.com", title="GitHub"), fetch_metadata=False)
    create_bookmark(db_session, BookmarkCreate(url="https://example.com", title="Example"), fetch_metadata=False)

    html = ie.export_bookmarks_to_netscape(db_session)

    assert "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html
    assert "https://github.com" in html
    assert "https://example.com" in html
    assert "GitHub" in html
    assert "Example" in html