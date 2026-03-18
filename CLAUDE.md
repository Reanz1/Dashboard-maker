# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A minimalist Flask-based home server dashboard for self-hosters. Zero-database architecture using JSON flat-files for storage. Features a dynamic theme system with in-browser HTML/CSS editing.

## Development Commands

```bash
# Local development
pip install -r requirements.txt
python app.py                    # Runs on http://localhost:5000

# Docker
docker-compose up -d             # Production with persistent volumes
docker build -t dashboard-maker . && docker run -p 5000:5000 -v ./data:/data -v ./images:/images dashboard-maker
```

There are no tests, linters, or build steps configured.

## Architecture

**Backend:** Single Flask app (`app.py`) serving a REST API and Jinja2 templates. Only dependency is Flask 3.0.2.

**Frontend:** Vanilla JS (`static/js/dashboard.js`) + Tailwind CSS via CDN. No build toolchain, no JS frameworks.

**Storage:** JSON files in `/data` directory (services.json, categories.json, config.json). User-created themes stored in `/data/themes/`. Images in `/images/`. All data files are auto-created on startup via `setup_environment()` if missing. In Docker, `/data` and `/images` are volume-mounted; locally they resolve to absolute paths at filesystem root.

## Theme System

Each theme is a **self-contained HTML file** in `templates/themes/` (default.html, neon.html, ocean.html) with inline CSS variables, Tailwind utilities, and full page structure. The legacy separate CSS files in `static/css/themes/` exist but themes are now self-contained.

**Theme resolution order:** User override in `/data/themes/<name>.html` → built-in in `templates/themes/<name>.html` → falls back to `templates/themes/default.html`. The `GET /` route reads the resolved HTML file directly and returns it (no Jinja2 rendering). All theme edits (PUT) write to the user themes dir so built-in files stay pristine.

User themes are created by cloning the currently active theme. The clone copies the resolved HTML to `/data/themes/<name>.html` and immediately switches to it.

## Key API Endpoints

All mutations go through `/api/*` endpoints returning JSON. The frontend uses fetch() and typically reloads the page after state changes (no SPA routing).

- `/api/services` - CRUD for dashboard service cards
- `/api/categories` - CRUD for service groupings
- `/api/themes` - Theme listing, cloning, editing (HTML content), deletion
- `/api/themes/<name>/reset` - Remove user override, restoring built-in version
- `/api/config` - Get/set active theme

## Frontend Patterns

- **Edit mode** toggled via `body.edit-mode` class; shows add/delete controls with `.edit-mode-only` visibility
- **Global state:** `globalCategories[]` array cached after fetch
- **Event delegation** on `#dynamic-content` for dynamically rendered service cards and category delete buttons
- **Custom confirmation modals** (`showConfirm()`) for all destructive actions — not browser confirm()
- **Accordion panels:** `<details>` elements for service/category/theme forms; opening one closes the others
- Service IDs are UUIDs generated server-side
- Theme names are sanitized to `[a-zA-Z0-9-]` lowercase on the backend
