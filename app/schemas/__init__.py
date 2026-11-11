from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List
from datetime import datetime


class BookmarkBase(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    favicon_url: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_favorite: bool = False
    is_archived: bool = False

    @validator("url")
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError("URL is required")
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class BookmarkCreate(BookmarkBase):
    pass


class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    favicon_url: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class BookmarkResponse(BookmarkBase):
    id: int
    normalized_url: str
    created_at: datetime
    updated_at: datetime
    tag_names: List[str] = []

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Category name is required")
        return v.strip()


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    bookmark_count: int = 0

    class Config:
        from_attributes = True


class TagBase(BaseModel):
    name: str

    @validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Tag name is required")
        return v.strip().lower()


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = None


class TagResponse(TagBase):
    id: int
    bookmark_count: int = 0

    class Config:
        from_attributes = True


class BookmarkListResponse(BaseModel):
    items: List[BookmarkResponse]
    total: int
    page: int
    page_size: int
    pages: int


class MetadataExtract(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    favicon_url: Optional[str] = None
    image_url: Optional[str] = None


class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: List[str] = []