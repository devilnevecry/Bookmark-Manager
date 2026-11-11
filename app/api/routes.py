"""API routes for bookmarks, categories, tags, and import/export."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

import app.schemas as schemas
import app.services.bookmark_service as bs
import app.services.import_export as ie
from app.database import get_db

router = APIRouter(prefix="/api")


# ---------- Bookmarks ----------

@router.get("/bookmarks", response_model=schemas.BookmarkListResponse)
def list_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    tag: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|title|domain)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    result = bs.get_bookmarks(
        db,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        tag=tag,
        is_favorite=is_favorite,
        is_archived=is_archived,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return {
        "items": result["items"],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }


@router.post("/bookmarks", response_model=schemas.BookmarkResponse, status_code=201)
def create_bookmark(
    bookmark_in: schemas.BookmarkCreate,
    db: Session = Depends(get_db),
):
    try:
        return bs.create_bookmark(db, bookmark_in, fetch_metadata=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bookmarks/{bookmark_id}", response_model=schemas.BookmarkResponse)
def get_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    bookmark = bs.get_bookmark(db, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


@router.put("/bookmarks/{bookmark_id}", response_model=schemas.BookmarkResponse)
def update_bookmark(
    bookmark_id: int,
    bookmark_in: schemas.BookmarkUpdate,
    db: Session = Depends(get_db),
):
    bookmark = bs.update_bookmark(db, bookmark_id, bookmark_in)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


@router.delete("/bookmarks/{bookmark_id}", status_code=204)
def delete_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    success = bs.delete_bookmark(db, bookmark_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return None


@router.post("/bookmarks/{bookmark_id}/favorite", response_model=schemas.BookmarkResponse)
def favorite_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    bookmark = bs.toggle_favorite(db, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


@router.post("/bookmarks/{bookmark_id}/archive", response_model=schemas.BookmarkResponse)
def archive_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    bookmark = bs.archive_bookmark(db, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


@router.post("/bookmarks/{bookmark_id}/restore", response_model=schemas.BookmarkResponse)
def restore_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    bookmark = bs.restore_bookmark(db, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


# ---------- Categories ----------

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    categories = bs.get_categories(db)
    result = []
    for cat in categories:
        count = len(cat.bookmarks)
        result.append(schemas.CategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            created_at=cat.created_at,
            bookmark_count=count,
        ))
    return result


@router.post("/categories", response_model=schemas.CategoryResponse, status_code=201)
def create_category(category_in: schemas.CategoryCreate, db: Session = Depends(get_db)):
    try:
        return bs.create_category(db, category_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/categories/{category_id}", response_model=schemas.CategoryResponse)
def update_category(
    category_id: int,
    category_in: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
):
    try:
        category = bs.update_category(db, category_id, category_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    count = len(category.bookmarks)
    return schemas.CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        created_at=category.created_at,
        bookmark_count=count,
    )


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    success = bs.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return None


# ---------- Tags ----------

@router.get("/tags", response_model=List[schemas.TagResponse])
def list_tags(db: Session = Depends(get_db)):
    tags = bs.get_tags(db)
    result = []
    for tag in tags:
        count = len(tag.bookmarks)
        result.append(schemas.TagResponse(
            id=tag.id,
            name=tag.name,
            bookmark_count=count,
        ))
    return result


@router.post("/tags", response_model=schemas.TagResponse, status_code=201)
def create_tag(tag_in: schemas.TagCreate, db: Session = Depends(get_db)):
    try:
        return bs.create_tag(db, tag_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/tags/{tag_id}", response_model=schemas.TagResponse)
def update_tag(tag_id: int, tag_in: schemas.TagUpdate, db: Session = Depends(get_db)):
    try:
        tag = bs.update_tag(db, tag_id, tag_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    count = len(tag.bookmarks)
    return schemas.TagResponse(id=tag.id, name=tag.name, bookmark_count=count)


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    success = bs.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return None


@router.post("/bookmarks/{bookmark_id}/tags/{tag_name}", response_model=schemas.BookmarkResponse)
def add_tag_to_bookmark(bookmark_id: int, tag_name: str, db: Session = Depends(get_db)):
    bookmark = bs.add_tag_to_bookmark(db, bookmark_id, tag_name)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


@router.delete("/bookmarks/{bookmark_id}/tags/{tag_id}", status_code=204)
def remove_tag_from_bookmark(bookmark_id: int, tag_id: int, db: Session = Depends(get_db)):
    success = bs.remove_tag_from_bookmark(db, bookmark_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag association not found")
    return None


# ---------- Import / Export ----------

@router.post("/import", response_model=schemas.ImportResult)
def import_bookmarks(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read().decode("utf-8", errors="ignore")
    return ie.import_netscape_html(db, content)


@router.get("/export")
def export_bookmarks(db: Session = Depends(get_db)):
    html = ie.export_bookmarks_to_netscape(db)
    return StreamingResponse(
        iter([html]),
        media_type="text/html",
        headers={"Content-Disposition": 'attachment; filename="bookmarks.html"'},
    )