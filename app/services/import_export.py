"""Import/Export service for Netscape Bookmark HTML format."""

import re
from typing import List, Optional
from html.parser import HTMLParser
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom import minidom

from sqlalchemy.orm import Session
from sqlalchemy import select, func

import app.models as models
import app.schemas as schemas
from app.services.bookmark_service import create_bookmark, get_bookmarks
from app.services.url_utils import normalize_url, extract_domain


class NetscapeBookmarkParser(HTMLParser):
    """Parses Netscape Bookmark HTML format."""

    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self.folder_stack = []
        self._in_a_tag = False
        self._in_h3 = False
        self._current_attrs = {}
        self._current_text = ""
        self._folders = []

    @property
    def current_folder(self):
        return self.folder_stack[-1] if self.folder_stack else None

    def handle_starttag(self, tag, attrs):
        if tag == "dl":
            pass
        elif tag == "dt":
            pass
        elif tag == "a":
            self._in_a_tag = True
            self._current_attrs = dict(attrs)
            self._current_text = ""
        elif tag == "h3":
            self._in_h3 = True
            self._current_text = ""

    def handle_endtag(self, tag):
        if tag == "a":
            self._in_a_tag = False
            href = self._current_attrs.get("href", "")
            title = self._current_text.strip()
            if href and title:
                self.bookmarks.append({
                    "url": href,
                    "title": title,
                    "folder": self.current_folder,
                })
        elif tag == "h3":
            self._in_h3 = False
            folder_name = self._current_text.strip()
            if folder_name:
                self.folder_stack.append(folder_name)
                self._folders.append(folder_name)
        elif tag == "dl":
            if self.folder_stack:
                self.folder_stack.pop()

    def handle_data(self, data):
        if self._in_a_tag or self._in_h3:
            self._current_text += data


def parse_netscape_html(html_content: str) -> dict:
    """Parse Netscape Bookmark HTML and return bookmarks and folders."""
    parser = NetscapeBookmarkParser()
    parser.feed(html_content)

    # Separate folders from bookmarks
    folders = list(dict.fromkeys(parser._folders))  # Preserve order, remove duplicates

    return {
        "bookmarks": parser.bookmarks,
        "folders": folders,
    }


def export_bookmarks_to_netscape(db: Session) -> str:
    """Export all bookmarks to Netscape Bookmark HTML format."""
    bookmarks = db.execute(select(models.Bookmark).order_by(models.Bookmark.created_at.desc())).scalars().all()

    lines = []
    lines.append('<!DOCTYPE NETSCAPE-Bookmark-file-1>')
    lines.append('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">')
    lines.append('<Title>Bookmarks</Title>')
    lines.append('<H1>Bookmarks</H1>')
    lines.append('<DL><p>')

    # Group by category
    uncategorized = []
    categorized = {}

    for bm in bookmarks:
        if bm.category_id:
            cat = db.get(models.Category, bm.category_id)
            cat_name = cat.name if cat else "Uncategorized"
        else:
            cat_name = None

        if cat_name:
            if cat_name not in categorized:
                categorized[cat_name] = []
            categorized[cat_name].append(bm)
        else:
            uncategorized.append(bm)

    # Add uncategorized bookmarks first
    if uncategorized:
        lines.append('<DT><H3>Uncategorized</H3>')
        lines.append('<DL><p>')
        for bm in uncategorized:
            lines.append(_format_bookmark_netscape(bm))
        lines.append('</DL><p>')

    # Add categorized bookmarks
    for cat_name, cat_bookmarks in categorized.items():
        lines.append(f'<DT><H3>{cat_name}</H3>')
        lines.append('<DL><p>')
        for bm in cat_bookmarks:
            lines.append(_format_bookmark_netscape(bm))
        lines.append('</DL><p>')

    lines.append('</DL><p>')

    return "\n".join(lines)


def _format_bookmark_netscape(bm: models.Bookmark) -> str:
    """Format a single bookmark in Netscape format."""
    tags = ",".join(bm.tag_names)
    desc = bm.description or ""
    return f'<DT><A HREF="{bm.url}" ADD_DATE="{int(bm.created_at.timestamp())}" TAGS="{tags}">{bm.title}</A>'


def import_netscape_html(db: Session, html_content: str) -> schemas.ImportResult:
    """Import bookmarks from Netscape Bookmark HTML."""
    parsed = parse_netscape_html(html_content)
    imported = 0
    skipped = 0
    errors = []

    # Create categories for folders
    folder_categories = {}
    for folder_name in parsed["folders"]:
        if not folder_name:
            continue
        try:
            # Check if category exists
            existing = db.execute(
                select(models.Category).where(func.lower(models.Category.name) == folder_name.lower())
            ).scalar_one_or_none()
            if existing:
                folder_categories[folder_name] = existing.id
            else:
                cat = models.Category(name=folder_name)
                db.add(cat)
                db.flush()
                folder_categories[folder_name] = cat.id
        except Exception as e:
            errors.append(f"Failed to create category '{folder_name}': {str(e)}")

    # Import bookmarks
    for bm_data in parsed["bookmarks"]:
        url = bm_data.get("url", "").strip()
        title = bm_data.get("title", "").strip() or url

        if not url or not url.startswith(("http://", "https://")):
            skipped += 1
            continue

        # Check for duplicate
        normalized = normalize_url(url)
        existing = db.execute(
            select(models.Bookmark).where(models.Bookmark.normalized_url == normalized)
        ).scalar_one_or_none()
        if existing:
            skipped += 1
            continue

        category_id = None
        folder = bm_data.get("folder")
        if folder and folder in folder_categories:
            category_id = folder_categories[folder]

        try:
            domain = extract_domain(url)
            bookmark = models.Bookmark(
                url=url,
                normalized_url=normalized,
                title=title,
                domain=domain,
                category_id=category_id,
            )
            db.add(bookmark)
            imported += 1
        except Exception as e:
            errors.append(f"Failed to import '{url}': {str(e)}")
            skipped += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        errors.append(f"Commit failed: {str(e)}")

    return schemas.ImportResult(imported=imported, skipped=skipped, errors=errors)