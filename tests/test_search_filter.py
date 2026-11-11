"""Tests for search, filter, and sort."""

import pytest
from app.services import bookmark_service as bs
from app.schemas import BookmarkCreate


def test_search_bookmarks_by_title(db_session):
    """Test searching bookmarks by title."""
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site1.com", title="Python Tutorial"), fetch_metadata=False)
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site2.com", title="JavaScript Guide"), fetch_metadata=False)

    result = bs.get_bookmarks(db_session, search="Python")
    assert result["total"] == 1
    assert result["items"][0].title == "Python Tutorial"


def test_search_bookmarks_by_url(db_session):
    """Test searching bookmarks by URL."""
    bs.create_bookmark(db_session, BookmarkCreate(url="https://github.com/user/repo", title="Repo"), fetch_metadata=False)

    result = bs.get_bookmarks(db_session, search="github.com")
    assert result["total"] == 1


def test_search_bookmarks_by_domain(db_session):
    """Test searching bookmarks by domain."""
    bs.create_bookmark(db_session, BookmarkCreate(url="https://example.com/page1", title="Page 1"), fetch_metadata=False)
    bs.create_bookmark(db_session, BookmarkCreate(url="https://other.com/page2", title="Page 2"), fetch_metadata=False)

    result = bs.get_bookmarks(db_session, search="example.com")
    assert result["total"] == 1


def test_filter_favorite(db_session):
    """Test filtering by favorite status."""
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site1.com", title="Site 1", is_favorite=True), fetch_metadata=False)
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site2.com", title="Site 2"), fetch_metadata=False)

    result = bs.get_bookmarks(db_session, is_favorite=True)
    assert result["total"] == 1
    assert result["items"][0].is_favorite is True


def test_filter_archived(db_session):
    """Test filtering by archived status."""
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site1.com", title="Site 1"), fetch_metadata=False)
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site2.com", title="Site 2"), fetch_metadata=False)

    # Archive one
    from app.models import Bookmark
    bookmarks = bs.get_bookmarks(db_session)["items"]
    bs.archive_bookmark(db_session, bookmarks[0].id)

    result = bs.get_bookmarks(db_session, is_archived=True)
    assert result["total"] == 1

    result_all = bs.get_bookmarks(db_session)
    assert result_all["total"] == 1  # Default excludes archived


def test_filter_by_category(db_session):
    """Test filtering by category."""
    from app.models import Category
    category = Category(name="Test Category")
    db_session.add(category)
    db_session.commit()

    bs.create_bookmark(db_session, BookmarkCreate(url="https://site1.com", title="Site 1", category_id=category.id), fetch_metadata=False)
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site2.com", title="Site 2"), fetch_metadata=False)

    result = bs.get_bookmarks(db_session, category_id=category.id)
    assert result["total"] == 1


def test_sort_by_title(db_session):
    """Test sorting by title."""
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site1.com", title="Zebra"), fetch_metadata=False)
    bs.create_bookmark(db_session, BookmarkCreate(url="https://site2.com", title="Apple"), fetch_metadata=False)

    result = bs.get_bookmarks(db_session, sort_by="title", sort_order="asc")
    assert result["items"][0].title == "Apple"
    assert result["items"][1].title == "Zebra"


def test_sort_by_domain(db_session):
    """Test sorting by domain."""
    bs.create_bookmark(db_session, BookmarkCreate(url="https://zsite.com", title="Z"), fetch_metadata=False)
    bs.create_bookmark(db_session, BookmarkCreate(url="https://asite.com", title="A"), fetch_metadata=False)

    result = bs.get_bookmarks(db_session, sort_by="domain", sort_order="asc")
    assert result["items"][0].domain == "asite.com"
    assert result["items"][1].domain == "zsite.com"


def test_pagination(db_session):
    """Test pagination of bookmarks."""
    for i in range(25):
        bs.create_bookmark(db_session, BookmarkCreate(url=f"https://site{i}.com", title=f"Site {i}"), fetch_metadata=False)

    result = bs.get_bookmarks(db_session, page=1, page_size=10)
    assert result["total"] == 25
    assert result["page"] == 1
    assert result["pages"] == 3
    assert len(result["items"]) == 10

    result_page2 = bs.get_bookmarks(db_session, page=2, page_size=10)
    assert result_page2["page"] == 2
    assert len(result_page2["items"]) == 10