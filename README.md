# Dashboard-maker

A sleek, lightweight home server dashboard built with Flask.

Built for self-hosters who want one page that links to everything they run, without config files to hand-edit, a database to maintain, or a build step to run. Everything — services, categories, even the theme's own HTML — is managed from the browser, and the whole state of the dashboard is three JSON files and a folder of icons.

## 😊 Examples

https://github.com/user-attachments/assets/ec1ab340-0e73-4aa1-a94a-6adbee43263a

https://github.com/user-attachments/assets/e57e59e4-062c-404d-9746-2b031dbc6048

https://github.com/user-attachments/assets/8a50a0ed-3003-4ca6-acd3-6c2a34d0beb3

## 🚀 Key Features

**Manage everything from the page.** Flip on edit mode to add, edit, reorder and delete service cards, and to create, rename and delete categories. Nothing needs a restart, and nothing needs the source.

**Live reachability.** Each card shows whether its service is answering. Checks run server-side and in parallel, refresh every minute, and accept self-signed certificates — the question is "is it up", not "is its certificate trustworthy". Any response counts, so a login page or a 404 still reads as up.

**Search.** Filters cards as you type, across name, description, URL and category.

**Drag to reorder.** Cards move within their category, and the order sticks.

**Service icons.** Upload a PNG, JPG, GIF, SVG, WEBP or ICO from the service panel, or pick one you already uploaded. Uploads never overwrite an existing icon — a repeat name gets a suffix.

**Themes you can edit in the browser.** Three ship with the app — Default, Neon and Ocean. Clone any of them and a full HTML editor opens right there; save and the page is restyled. One button resets a theme to the version that shipped.

**Zero-database.** Three JSON files and an images folder. Back up the dashboard by copying a directory. Writes are atomic, so an interrupted save can't truncate your services.

**Container-ready.** Python-slim base, one dependency (Flask), no CDN calls at runtime — Tailwind and Inter are served from the image.

## 📦 Deployment

```yaml
services:
  dashboard:
    image: randomsi/dashboard-maker:latest
    container_name: dashboard-maker
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./data:/data
      - ./images:/images
```

```bash
docker compose up -d
```

Then open `http://<your-server>:5000`.

Pin a release instead of `latest` if you'd rather upgrade deliberately — `randomsi/dashboard-maker:1.1.0`.

### 🗂️ What's in the volumes

| Path | Holds |
| --- | --- |
| `/data/services.json` | Your service cards |
| `/data/categories.json` | Category names and their order |
| `/data/config.json` | The active theme |
| `/data/themes/` | Themes you cloned or edited, as `.html` files |
| `/images/` | Uploaded service icons |

All of it is created on first start if missing. Nothing in either volume is rewritten on startup, so upgrading is a pull and a recreate against the same volumes.

### 🐍 Running from source

```bash
pip install -r requirements.txt
python app.py          # http://localhost:5000
```

Heads up: `/data` and `/images` are absolute paths, so running outside a container creates them at the filesystem root and needs the permissions to do so.

## 🎨 Theming

Themes are self-contained HTML files. Each one is the entire page — structure, CSS variables, Tailwind classes — and the app serves it as-is. The controls, dialogs and their styling are injected at runtime by `dashboard.js`, so a theme doesn't have to implement any of that; it just has to describe how the page should look.

To make your own:

1. Switch to whichever built-in theme is closest to what you want.
2. Open the theme panel in edit mode, type a name, and clone it. The clone lands in `/data/themes/<name>.html` and becomes active immediately.
3. Edit it in the built-in editor and save. Reset puts it back to the version it was cloned from.

Because the editor takes whole HTML, you can use your favorite AI to write a new one and paste the result back! 😆

https://github.com/user-attachments/assets/0019ac4a-557c-4297-b9e2-562fc4962f83

Two things worth knowing. Editing a built-in theme never touches the file in the image — the edit is saved as an override in `/data/themes/`, which is also why Reset can always get you back. And themes are served raw, not rendered as templates, so a theme reads its data from the API at runtime rather than through Jinja2.

## 🔌 API

Everything the UI does goes through these.

| Endpoint | Methods | Purpose |
| --- | --- | --- |
| `/api/services` | GET, POST | List and add service cards |
| `/api/services/<id>` | PUT, DELETE | Update or remove one |
| `/api/services/reorder` | POST | Persist card order |
| `/api/status` | GET | Reachability per service, cached 30s |
| `/api/categories` | GET, POST | List and add categories |
| `/api/categories/<name>` | PUT, DELETE | Rename, or delete with `?reassign=<target>` |
| `/api/images` | GET, POST | List and upload icons |
| `/api/themes` | GET, POST | List themes, clone the active one |
| `/api/themes/<name>` | GET, PUT, DELETE | Read, save and remove theme HTML |
| `/api/themes/<name>/reset` | POST | Drop the override, restore the built-in |
| `/api/config` | GET, POST | Read and set the active theme |

## 📄 License

MIT. See [LICENSE](LICENSE) — it also ships inside the image at `/app/LICENSE`.
