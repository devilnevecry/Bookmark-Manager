"""Tests for categories and tags."""

import pytest
from app.services import bookmark_service as bs
from app.schemas import CategoryCreate, CategoryUpdate, TagCreate, TagUpdate


def test_create_category(db_session):
    """Test creating a category."""
    category_in = CategoryCreate(name="Development", description="Dev links")
    category = bs.create_category(db_session, category_in)

    assert category.id is not None
    assert category.name == "Development"
    assert category.description == "Dev links"


def test_create_duplicate_category(db_session):
    """Test that duplicate category names are rejected."""
    category_in = CategoryCreate(name="Development")
    bs.create_category(db_session, category_in)

    with pytest.raises(ValueError, match="already exists"):
        bs.create_category(db_session, category_in)


def test_get_categories(db_session):
    """Test retrieving all categories."""
    bs.create_category(db_session, CategoryCreate(name="Cat A"))
    bs.create_category(db_session, CategoryCreate(name="Cat B"))

    categories = bs.get_categories(db_session)
    assert len(categories) == 2


def test_update_category(db_session):
    """Test updating a category."""
    category = bs.create_category(db_session, CategoryCreate(name="Old Name"))

    update = CategoryUpdate(name="New Name", description="New desc")
    updated = bs.update_category(db_session, category.id, update)

    assert updated.name == "New Name"
    assert updated.description == "New desc"


def test_delete_category(db_session):
    """Test deleting a category."""
    category = bs.create_category(db_session, CategoryCreate(name="To Delete"))

    success = bs.delete_category(db_session, category.id)
    assert success is True

    assert bs.get_category(db_session, category.id) is None


def test_create_tag(db_session):
    """Test creating a tag."""
    tag_in = TagCreate(name="important")
    tag = bs.create_tag(db_session, tag_in)

    assert tag.id is not None
    assert tag.name == "important"


def test_create_duplicate_tag(db_session):
    """Test that duplicate tag names are rejected."""
    tag_in = TagCreate(name="important")
    bs.create_tag(db_session, tag_in)

    with pytest.raises(ValueError, match="already exists"):
        bs.create_tag(db_session, tag_in)


def test_tag_case_insensitive(db_session):
    """Test that tag names are case-insensitive (stored lowercase)."""
    tag = bs.create_tag(db_session, TagCreate(name="IMPORTANT"))
    assert tag.name == "important"


def test_add_tag_to_bookmark(db_session):
    """Test adding a tag to a bookmark."""
    from app.schemas import BookmarkCreate
    bookmark = bs.create_bookmark(
        db_session, BookmarkCreate(url="https://example.com", title="Example"),
        fetch_metadata=False,
    )

    updated = bs.add_tag_to_bookmark(db_session, bookmark.id, "important")
    assert updated is not None

    tag = bs.get_tag_by_name(db_session, "important")
    assert tag is not None


def test_remove_tag_from_bookmark(db_session):
    """Test removing a tag from a bookmark."""
    from app.schemas import BookmarkCreate
    bookmark = bs.create_bookmark(
        db_session, BookmarkCreate(url="https://example.com", title="Example"),
        fetch_metadata=False,
    )
    bs.add_tag_to_bookmark(db_session, bookmark.id, "important")

    tag = bs.get_tag_by_name(db_session, "important")
    success = bs.remove_tag_from_bookmark(db_session, bookmark.id, tag.id)
    assert success is True

    # Try removing again - should fail
    success_again = bs.remove_tag_from_bookmark(db_session, bookmark.id, tag.id)
    assert success_again is False