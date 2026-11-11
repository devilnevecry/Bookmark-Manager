from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    normalized_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    category: Mapped[Optional["Category"]] = relationship(back_populates="bookmarks", lazy="selectin")
    tags: Mapped[List["BookmarkTag"]] = relationship(back_populates="bookmark", cascade="all, delete-orphan", lazy="selectin")

    @property
    def tag_names(self) -> List[str]:
        return [bt.tag.name for bt in self.tags]


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    bookmarks: Mapped[List["Bookmark"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True, unique=True)

    bookmarks: Mapped[List["BookmarkTag"]] = relationship(back_populates="tag", cascade="all, delete-orphan")


class BookmarkTag(Base):
    __tablename__ = "bookmark_tags"

    bookmark_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookmarks.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    bookmark: Mapped["Bookmark"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="bookmarks")