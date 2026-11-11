"""Bookmark business logic service."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, select, and_

import app.models as models
import app.schemas as schemas
from app.services.metadata_extractor import extract_metadata
from app.services.url_utils import normalize_url, extract_domain


def get_bookmarks(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    tag: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """Get bookmarks with filtering, search, sorting, and pagination."""
    query = select(models.Bookmark)

    # Exclude archived by default unless specified
    if is_archived is None:
        query = query.where(models.Bookmark.is_archived == False)

    if is_archived is not None:
        query = query.where(models.Bookmark.is_archived == is_archived)

    if is_favorite is not None:
        query = query.where(models.Bookmark.is_favorite == is_favorite)

    if category_id is not None:
        query = query.where(models.Bookmark.category_id == category_id)

    if tag:
        query = query.join(models.Bookmark.tags).join(models.Tag).where(
            models.Tag.name == tag.lower()
        )

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(models.Bookmark.title).like(search_term),
                func.lower(models.Bookmark.description).like(search_term),
                func.lower(models.Bookmark.url).like(search_term),
                func.lower(models.Bookmark.domain).like(search_term),
            )
        )

    # Sorting
    sort_column = getattr(models.Bookmark, sort_by, models.Bookmark.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    bookmarks = db.execute(query).scalars().all()
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "items": bookmarks,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


def get_bookmark(db: Session, bookmark_id: int) -> Optional[models.Bookmark]:
    """Get a single bookmark by ID."""
    return db.get(models.Bookmark, bookmark_id)


def create_bookmark(db: Session, bookmark_in: schemas.BookmarkCreate, fetch_metadata: bool = True) -> models.Bookmark:
    """Create a new bookmark, optionally fetching metadata."""
    url = bookmark_in.url.strip()
    normalized = normalize_url(url)
    domain = extract_domain(url)

    # Check for duplicate
    existing = db.execute(
        select(models.Bookmark).where(models.Bookmark.normalized_url == normalized)
    ).scalar_one_or_none()
    if existing:
        raise ValueError("A bookmark with this URL already exists")

    # Prepare data
    title = bookmark_in.title or ""
    description = bookmark_in.description
    favicon_url = bookmark_in.favicon_url
    image_url = bookmark_in.image_url

    # Fetch metadata if not provided
    if fetch_metadata and (not title or not description):
        try:
            meta = extract_metadata(url)
            if meta.get("title") and not title:
                title = meta["title"]
            if meta.get("description") and not description:
                description = meta["description"]
            if meta.get("favicon_url") and not favicon_url:
                favicon_url = meta["favicon_url"]
            if meta.get("image_url") and not image_url:
                image_url = meta["image_url"]
            if not domain and meta.get("domain"):
                domain = meta["domain"]
        except Exception:
            pass

    if not title:
        title = url

    bookmark = models.Bookmark(
        url=url,
        normalized_url=normalized,
        title=title,
        description=description,
        domain=domain,
        favicon_url=favicon_url,
        image_url=image_url,
        category_id=bookmark_in.category_id,
        is_favorite=bookmark_in.is_favorite,
        is_archived=bookmark_in.is_archived,
    )
    db.add(bookmark)
    db.flush()

    # Handle tags
    if hasattr(bookmark_in, "tag_names") and bookmark_in.tag_names:
        _set_tags(db, bookmark, bookmark_in.tag_names)

    db.commit()
    db.refresh(bookmark)
    return bookmark


def update_bookmark(db: Session, bookmark_id: int, bookmark_in: schemas.BookmarkUpdate) -> Optional[models.Bookmark]:
    """Update an existing bookmark."""
    bookmark = db.get(models.Bookmark, bookmark_id)
    if not bookmark:
        return None

    update_data = bookmark_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bookmark, field, value)

    db.commit()
    db.refresh(bookmark)
    return bookmark


def delete_bookmark(db: Session, bookmark_id: int) -> bool:
    """Delete a bookmark by ID."""
    bookmark = db.get(models.Bookmark, bookmark_id)
    if not bookmark:
        return False
    db.delete(bookmark)
    db.commit()
    return True


def toggle_favorite(db: Session, bookmark_id: int) -> Optional[models.Bookmark]:
    """Toggle favorite status."""
    bookmark = db.get(models.Bookmark, bookmark_id)
    if not bookmark:
        return None
    bookmark.is_favorite = not bookmark.is_favorite
    db.commit()
    db.refresh(bookmark)
    return bookmark


def archive_bookmark(db: Session, bookmark_id: int) -> Optional[models.Bookmark]:
    """Archive a bookmark."""
    bookmark = db.get(models.Bookmark, bookmark_id)
    if not bookmark:
        return None
    bookmark.is_archived = True
    db.commit()
    db.refresh(bookmark)
    return bookmark


def restore_bookmark(db: Session, bookmark_id: int) -> Optional[models.Bookmark]:
    """Restore an archived bookmark."""
    bookmark = db.get(models.Bookmark, bookmark_id)
    if not bookmark:
        return None
    bookmark.is_archived = False
    db.commit()
    db.refresh(bookmark)
    return bookmark


def _set_tags(db: Session, bookmark: models.Bookmark, tag_names: List[str]):
    """Set tags for a bookmark, creating tags as needed."""
    # Clear existing tags
    bookmark.tags = []

    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag = db.execute(select(models.Tag).where(models.Tag.name == name)).scalar_one_or_none()
        if not tag:
            tag = models.Tag(name=name)
            db.add(tag)
            db.flush()
        bookmark.tags.append(models.BookmarkTag(tag_id=tag.id))


def get_categories(db: Session) -> List[models.Category]:
    """Get all categories."""
    return db.execute(select(models.Category).order_by(models.Category.name)).scalars().all()


def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    """Get a category by ID."""
    return db.get(models.Category, category_id)


def create_category(db: Session, category_in: schemas.CategoryCreate) -> models.Category:
    """Create a new category."""
    existing = db.execute(
        select(models.Category).where(func.lower(models.Category.name) == category_in.name.lower())
    ).scalar_one_or_none()
    if existing:
        raise ValueError("A category with this name already exists")

    category = models.Category(name=category_in.name, description=category_in.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, category_in: schemas.CategoryUpdate) -> Optional[models.Category]:
    """Update a category."""
    category = db.get(models.Category, category_id)
    if not category:
        return None

    if category_in.name is not None:
        existing = db.execute(
            select(models.Category).where(
                func.lower(models.Category.name) == category_in.name.lower(),
                models.Category.id != category_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("A category with this name already exists")
        category.name = category_in.name

    if category_in.description is not None:
        category.description = category_in.description

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> bool:
    """Delete a category (bookmarks in it will have category_id set to NULL)."""
    category = db.get(models.Category, category_id)
    if not category:
        return False
    db.delete(category)
    db.commit()
    return True


def get_tags(db: Session) -> List[models.Tag]:
    """Get all tags."""
    return db.execute(select(models.Tag).order_by(models.Tag.name)).scalars().all()


def get_tag(db: Session, tag_id: int) -> Optional[models.Tag]:
    """Get a tag by ID."""
    return db.get(models.Tag, tag_id)


def get_tag_by_name(db: Session, name: str) -> Optional[models.Tag]:
    """Get a tag by name."""
    return db.execute(select(models.Tag).where(models.Tag.name == name.lower())).scalar_one_or_none()


def create_tag(db: Session, tag_in: schemas.TagCreate) -> models.Tag:
    """Create a new tag."""
    existing = get_tag_by_name(db, tag_in.name)
    if existing:
        raise ValueError("A tag with this name already exists")

    tag = models.Tag(name=tag_in.name.lower())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def update_tag(db: Session, tag_id: int, tag_in: schemas.TagUpdate) -> Optional[models.Tag]:
    """Update a tag."""
    tag = db.get(models.Tag, tag_id)
    if not tag:
        return None

    if tag_in.name is not None:
        existing = get_tag_by_name(db, tag_in.name)
        if existing and existing.id != tag_id:
            raise ValueError("A tag with this name already exists")
        tag.name = tag_in.name.lower()

    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag_id: int) -> bool:
    """Delete a tag."""
    tag = db.get(models.Tag, tag_id)
    if not tag:
        return False
    db.delete(tag)
    db.commit()
    return True


def add_tag_to_bookmark(db: Session, bookmark_id: int, tag_name: str) -> Optional[models.Bookmark]:
    """Add a tag to a bookmark."""
    bookmark = db.get(models.Bookmark, bookmark_id)
    if not bookmark:
        return None

    tag_name = tag_name.strip().lower()
    if not tag_name:
        return bookmark

    tag = get_tag_by_name(db, tag_name)
    if not tag:
        tag = models.Tag(name=tag_name)
        db.add(tag)
        db.flush()

    # Check if already associated
    existing = db.execute(
        select(models.BookmarkTag).where(
            models.BookmarkTag.bookmark_id == bookmark_id,
            models.BookmarkTag.tag_id == tag.id,
        )
    ).scalar_one_or_none()
    if not existing:
        db.add(models.BookmarkTag(bookmark_id=bookmark_id, tag_id=tag.id))
        db.commit()
        db.refresh(bookmark)

    return bookmark


def remove_tag_from_bookmark(db: Session, bookmark_id: int, tag_id: int) -> bool:
    """Remove a tag from a bookmark."""
    association = db.execute(
        select(models.BookmarkTag).where(
            models.BookmarkTag.bookmark_id == bookmark_id,
            models.BookmarkTag.tag_id == tag_id,
        )
    ).scalar_one_or_none()
    if not association:
        return False
    db.delete(association)
    db.commit()
    return True