# Bookmark Manager

English | [Русский](README.ru.md)

A local web application for managing bookmarks with automatic metadata extraction, categories, tags, search, filtering, and import/export. Built with Python, FastAPI, SQLAlchemy, and SQLite. Designed as a self-hosted, single-user bookmark manager for personal use.

## Badges

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/<your-username>/bookmark-manager/actions/workflows/tests.yml/badge.svg)](https://github.com/<your-username>/bookmark-manager/actions/workflows/tests.yml)

> Replace `<your-username>` in the badge URLs above with your actual GitHub username after creating the repository.

## Features

### Bookmark management
- Add bookmarks by URL; title, description, Open Graph image, and favicon are extracted automatically
- Edit bookmark title, description, category, and tags
- Delete bookmarks
- Add or remove bookmarks from favorites
- Archive and restore bookmarks
- Open the original page or copy the URL to clipboard

### Automatic metadata extraction
- Page title priority: `og:title` → `twitter:title` → HTML `<title>`
- Description priority: `og:description` → `twitter:description` → `<meta name="description">`
- Open Graph image and favicon extraction
- Domain extraction from URL
- Graceful fallback: if extraction fails, the link can still be saved manually
- Errors on external sites never crash the application

### Categories and tags
- Create, edit, and delete categories
- Assign categories to bookmarks
- Add multiple tags to a single bookmark (many-to-many relationship)
- Filter bookmarks by category or tag
- No duplicate category or tag names

### Search and filtering
- Full-text search across title, description, URL, and domain
- Filters: all bookmarks, favorites, archive, by category, by tag
- Sorting: by date added, by title, by domain
- Pagination

### Import and export
- Import Netscape Bookmark HTML (browser bookmarks export)
- Browser folder structure imported as categories
- Import report with imported count and skipped duplicates
- Export all bookmarks back to Netscape Bookmark HTML

### Interface
- Modern responsive UI with dark and light themes
- Sidebar with categories and tags
- Card-based bookmark layout
- Toast notifications for success and errors
- Modal dialogs for creating and editing bookmarks

## Technology stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Core application |
| FastAPI | REST API and web framework |
| SQLite | Local database |
| SQLAlchemy 2.x | ORM |
| Pydantic | Data validation |
| Jinja2 | HTML templates |
| httpx | HTTP client for metadata extraction |
| BeautifulSoup4 | HTML parsing |
| HTML/CSS/JavaScript | Frontend |
| pytest | Automated testing |

## Architecture

```
bookmark-manager/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # SQLAlchemy engine, session, base
│   ├── models/
│   │   └── bookmark.py         # Bookmark, Category, Tag, BookmarkTag models
│   ├── schemas/
│   │   └── __init__.py         # Pydantic validation schemas
│   ├── api/
│   │   └── routes.py           # REST API endpoints
│   ├── services/
│   │   ├── bookmark_service.py # Business logic (CRUD, search, tags, categories)
│   │   ├── metadata_extractor.py # Metadata extraction with SSRF protection
│   │   ├── import_export.py    # Netscape HTML import/export
│   │   └── url_utils.py        # URL normalization and validation
│   ├── templates/
│   │   └── index.html          # Jinja2 template
│   └── static/
│       ├── css/style.css       # Stylesheet
│       └── js/app.js           # Frontend application logic
├── tests/
│   ├── conftest.py             # Test fixtures and database setup
│   ├── fixtures/               # Local HTML test fixtures (no external sites)
│   ├── test_api.py             # API endpoint tests
│   ├── test_bookmarks.py       # Bookmark CRUD tests
│   ├── test_categories_tags.py # Category and tag tests
│   ├── test_import_export.py   # Import/export tests
│   ├── test_metadata.py        # Metadata extraction tests
│   ├── test_search_filter.py   # Search, filter, sort tests
│   └── test_security.py        # SSRF and URL validation tests
├── data/                       # SQLite database storage (gitignored)
├── .github/workflows/tests.yml # GitHub Actions CI
├── LICENSE                     # MIT License
├── pyproject.toml              # Project configuration and dependencies
└── README.md                   # This file
```

### Database models

**Bookmark** — `id`, `url`, `normalized_url` (unique), `title`, `description`, `domain`, `favicon_url`, `image_url`, `category_id`, `is_favorite`, `is_archived`, `created_at`, `updated_at`

**Category** — `id`, `name` (unique), `description`, `created_at`

**Tag** — `id`, `name` (unique, lowercase)

**BookmarkTag** — join table `bookmark_id`, `tag_id` with cascade delete

Business logic is separated from API handlers and HTML templates. URL normalization removes fragments, lowercases scheme/hostname, and preserves query parameters. SSRF protection blocks localhost, loopback, private/reserved IP ranges, and non-HTTP(S) schemes.

## Installation

### Requirements

- Python 3.11 or higher
- pip

### Windows (PowerShell)

```powershell
# Clone the repository
git clone https://github.com/<your-username>/bookmark-manager.git
cd bookmark-manager

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"
```

### Linux / macOS

```bash
# Clone the repository
git clone https://github.com/<your-username>/bookmark-manager.git
cd bookmark-manager

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

Replace `<your-username>` with your GitHub username.

## Usage

Start the application:

```bash
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

- **Web interface**: http://127.0.0.1:8000/
- **API documentation (Swagger UI)**: http://127.0.0.1:8000/docs
- **OpenAPI schema**: http://127.0.0.1:8000/openapi.json

Data is stored in `data/bookmarks.db` (SQLite). Your bookmarks persist across restarts.

### Main REST API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/bookmarks` | List bookmarks (search, filter, sort, pagination) |
| POST | `/api/bookmarks` | Create a bookmark |
| GET | `/api/bookmarks/{id}` | Get a bookmark by ID |
| PUT | `/api/bookmarks/{id}` | Update a bookmark |
| DELETE | `/api/bookmarks/{id}` | Delete a bookmark |
| POST | `/api/bookmarks/{id}/favorite` | Toggle favorite |
| POST | `/api/bookmarks/{id}/archive` | Archive a bookmark |
| POST | `/api/bookmarks/{id}/restore` | Restore an archived bookmark |
| GET | `/api/categories` | List categories |
| POST | `/api/categories` | Create a category |
| GET | `/api/tags` | List tags |
| POST | `/api/tags` | Create a tag |
| POST | `/api/import` | Import Netscape Bookmark HTML |
| GET | `/api/export` | Export bookmarks to Netscape Bookmark HTML |

### Importing bookmarks from a browser

1. Export your bookmarks from your browser (Chrome, Firefox, Edge, etc.) as an HTML file in Netscape Bookmark format.
2. Open the Bookmark Manager application.
3. Click **Import / Export** in the sidebar.
4. Select the exported HTML file and click **Import**.
5. Review the import report showing imported and skipped (duplicate) bookmarks.

Folder structure from your browser bookmarks is imported as categories.

## Testing

The project includes 66 automated tests. All tests use local HTML fixtures and mocks — no external websites are contacted.

```bash
python -m pytest
```

Tests cover bookmark CRUD, categories, tags, search, filtering, sorting, pagination, metadata extraction, SSRF protection, URL validation, import/export, and all API endpoints.

## Configuration

The application works without additional configuration. The SQLite database is created automatically in the `data/` directory on first run.

No environment variables are required. If you need to customize settings in the future, create a `.env` file based on `.env.example` (not provided by default).

## Limitations

- Single-user, local application; no user authentication or multi-user support.
- Metadata extraction is a best-effort process; some pages may block scraping or lack Open Graph tags.
- External images are not downloaded; only their URLs are stored.
- No JavaScript execution on third-party pages during metadata extraction.
- Designed for local deployment; not intended for public-facing internet hosting without additional security review.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
