"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_create_bookmark_api(client):
    """Test POST /api/bookmarks."""
    response = client.post("/api/bookmarks", json={
        "url": "https://example.com",
        "title": "Example",
        "description": "Test",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com"
    assert data["title"] == "Example"


def test_create_bookmark_api_duplicate(client):
    """Test duplicate URL rejection via API."""
    client.post("/api/bookmarks", json={
        "url": "https://example.com",
        "title": "Example",
    })
    response = client.post("/api/bookmarks", json={
        "url": "https://example.com",
        "title": "Example",
    })
    assert response.status_code == 400


def test_list_bookmarks_api(client):
    """Test GET /api/bookmarks."""
    client.post("/api/bookmarks", json={"url": "https://site1.com", "title": "Site 1"})
    client.post("/api/bookmarks", json={"url": "https://site2.com", "title": "Site 2"})

    response = client.get("/api/bookmarks")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_bookmark_api(client):
    """Test GET /api/bookmarks/{id}."""
    create = client.post("/api/bookmarks", json={"url": "https://example.com", "title": "Example"})
    bookmark_id = create.json()["id"]

    response = client.get(f"/api/bookmarks/{bookmark_id}")
    assert response.status_code == 200
    assert response.json()["id"] == bookmark_id


def test_update_bookmark_api(client):
    """Test PUT /api/bookmarks/{id}."""
    create = client.post("/api/bookmarks", json={"url": "https://example.com", "title": "Old"})
    bookmark_id = create.json()["id"]

    response = client.put(f"/api/bookmarks/{bookmark_id}", json={"title": "New"})
    assert response.status_code == 200
    assert response.json()["title"] == "New"


def test_delete_bookmark_api(client):
    """Test DELETE /api/bookmarks/{id}."""
    create = client.post("/api/bookmarks", json={"url": "https://example.com", "title": "Example"})
    bookmark_id = create.json()["id"]

    response = client.delete(f"/api/bookmarks/{bookmark_id}")
    assert response.status_code == 204

    response = client.get(f"/api/bookmarks/{bookmark_id}")
    assert response.status_code == 404


def test_create_category_api(client):
    """Test POST /api/categories."""
    response = client.post("/api/categories", json={"name": "Development", "description": "Dev"})
    assert response.status_code == 201
    assert response.json()["name"] == "Development"


def test_list_categories_api(client):
    """Test GET /api/categories."""
    client.post("/api/categories", json={"name": "Cat A"})
    client.post("/api/categories", json={"name": "Cat B"})

    response = client.get("/api/categories")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_tag_api(client):
    """Test POST /api/tags."""
    response = client.post("/api/tags", json={"name": "important"})
    assert response.status_code == 201
    assert response.json()["name"] == "important"


def test_list_tags_api(client):
    """Test GET /api/tags."""
    client.post("/api/tags", json={"name": "tag1"})
    client.post("/api/tags", json={"name": "tag2"})

    response = client.get("/api/tags")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_import_api(client):
    """Test POST /api/import."""
    html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p>
    <DT><A HREF="https://example.com" ADD_DATE="1234567890">Example</A>
</DL><p>"""

    response = client.post("/api/import", files={"file": ("bookmarks.html", html, "text/html")})
    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1


def test_export_api(client):
    """Test GET /api/export."""
    client.post("/api/bookmarks", json={"url": "https://example.com", "title": "Example"})

    response = client.get("/api/export")
    assert response.status_code == 200
    assert "NETSCAPE-Bookmark-file-1" in response.text
    assert "example.com" in response.text


def test_search_api(client):
    """Test search via API."""
    client.post("/api/bookmarks", json={"url": "https://python.org", "title": "Python"})
    client.post("/api/bookmarks", json={"url": "https://js.org", "title": "JavaScript"})

    response = client.get("/api/bookmarks?search=Python")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_invalid_url_api(client):
    """Test invalid URL rejection."""
    response = client.post("/api/bookmarks", json={"url": "not-a-url", "title": "Test"})
    assert response.status_code == 422

    response = client.post("/api/bookmarks", json={"url": "ftp://example.com", "title": "Test"})
    assert response.status_code == 422