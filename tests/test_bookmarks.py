"""Tests for bookmark CRUD operations."""

import pytest
from app.services import bookmark_service as bs
from app.schemas import BookmarkCreate, BookmarkUpdate
from app.models import Bookmark


def test_create_bookmark(db_session):
    """Test creating a bookmark."""
    bookmark_in = BookmarkCreate(
        url="https://example.com",
        title="Example",
        description="Test description",
    )
    bookmark = bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)

    assert bookmark.id is not None
    assert bookmark.url == "https://example.com"
    assert bookmark.title == "Example"
    assert bookmark.description == "Test description"
    assert bookmark.domain == "example.com"
    assert bookmark.normalized_url == "https://example.com/"
    assert bookmark.is_favorite is False
    assert bookmark.is_archived is False


def test_create_bookmark_duplicate_url(db_session):
    """Test that duplicate URLs are rejected."""
    bookmark_in = BookmarkCreate(url="https://example.com", title="Example")
    bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)

    with pytest.raises(ValueError, match="already exists"):
        bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)


def test_get_bookmark(db_session):
    """Test retrieving a bookmark by ID."""
    bookmark_in = BookmarkCreate(url="https://example.com", title="Example")
    bookmark = bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)

    fetched = bs.get_bookmark(db_session, bookmark.id)
    assert fetched is not None
    assert fetched.id == bookmark.id
    assert fetched.title == "Example"


def test_get_nonexistent_bookmark(db_session):
    """Test retrieving a nonexistent bookmark returns None."""
    result = bs.get_bookmark(db_session, 99999)
    assert result is None


def test_update_bookmark(db_session):
    """Test updating a bookmark."""
    bookmark_in = BookmarkCreate(url="https://example.com", title="Example")
    bookmark = bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)

    update = BookmarkUpdate(title="Updated Title", description="New description")
    updated = bs.update_bookmark(db_session, bookmark.id, update)

    assert updated.title == "Updated Title"
    assert updated.description == "New description"


def test_update_nonexistent_bookmark(db_session):
    """Test updating a nonexistent bookmark returns None."""
    update = BookmarkUpdate(title="Updated")
    result = bs.update_bookmark(db_session, 99999, update)
    assert result is None


def test_delete_bookmark(db_session):
    """Test deleting a bookmark."""
    bookmark_in = BookmarkCreate(url="https://example.com", title="Example")
    bookmark = bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)

    success = bs.delete_bookmark(db_session, bookmark.id)
    assert success is True

    fetched = bs.get_bookmark(db_session, bookmark.id)
    assert fetched is None


def test_delete_nonexistent_bookmark(db_session):
    """Test deleting a nonexistent bookmark returns False."""
    success = bs.delete_bookmark(db_session, 99999)
    assert success is False


def test_toggle_favorite(db_session):
    """Test toggling favorite status."""
    bookmark_in = BookmarkCreate(url="https://example.com", title="Example")
    bookmark = bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)

    toggled = bs.toggle_favorite(db_session, bookmark.id)
    assert toggled.is_favorite is True

    toggled_again = bs.toggle_favorite(db_session, bookmark.id)
    assert toggled_again.is_favorite is False


def test_archive_and_restore(db_session):
    """Test archiving and restoring a bookmark."""
    bookmark_in = BookmarkCreate(url="https://example.com", title="Example")
    bookmark = bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)

    archived = bs.archive_bookmark(db_session, bookmark.id)
    assert archived.is_archived is True

    restored = bs.restore_bookmark(db_session, bookmark.id)
    assert restored.is_archived is False


def test_bookmark_with_category(db_session):
    """Test creating a bookmark with a category."""
    from app.models import Category
    category = Category(name="Test Category")
    db_session.add(category)
    db_session.commit()

    bookmark_in = BookmarkCreate(
        url="https://example.com",
        title="Example",
        category_id=category.id,
    )
    bookmark = bs.create_bookmark(db_session, bookmark_in, fetch_metadata=False)
    assert bookmark.category_id == category.id


def test_url_normalization_removes_fragment(db_session):
    """Test that URL fragments are removed during normalization."""
    from app.services.url_utils import normalize_url
    normalized = normalize_url("https://example.com/page#section")
    assert normalized == "https://example.com/page"


def test_url_normalization_lowercase(db_session):
    """Test that scheme and hostname are lowercased."""
    from app.services.url_utils import normalize_url
    normalized = normalize_url("HTTPS://Example.COM/Page")
    assert normalized == "https://example.com/Page"