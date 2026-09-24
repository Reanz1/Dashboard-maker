import json
import os
import uuid
import re
import shutil
import ssl
import stat
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')

app.config['TEMPLATES_AUTO_RELOAD'] = True

DATA_DIR = '/data'
IMAGES_DIR = '/images'
USER_THEMES_DIR = os.path.join(DATA_DIR, 'themes')

SERVICES_FILE = os.path.join(DATA_DIR, 'services.json')
CATEGORIES_FILE = os.path.join(DATA_DIR, 'categories.json')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

DEFAULT_CATEGORIES = ["Media & Content", "Management & Network", "Ai & Generation"]
DEFAULT_CONFIG = {"theme": "default"}

BUILTIN_THEMES = ['default', 'neon', 'ocean']
BUILTIN_THEMES_DIR = os.path.join('templates', 'themes')

ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}

# Reachability checks are cheap but not free; serve a cached sweep for a while.
STATUS_TTL_SECONDS = 30
STATUS_TIMEOUT_SECONDS = 3
_status_cache = {'checked_at': 0.0, 'results': {}}

# Home servers run self-signed certs constantly; "is it answering" is the
# question here, not "is its certificate trustworthy".
UNVERIFIED_SSL = ssl.create_default_context()
UNVERIFIED_SSL.check_hostname = False
UNVERIFIED_SSL.verify_mode = ssl.CERT_NONE


# ── Setup ──

def setup_environment():
    for d in [DATA_DIR, IMAGES_DIR, USER_THEMES_DIR]:
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(SERVICES_FILE):
        with open(SERVICES_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'w') as f:
            json.dump(DEFAULT_CATEGORIES, f)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f)


setup_environment()


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data, path):
    """Write through a temp file in the same directory, then rename.

    os.replace is atomic, so a crash or a second writer can never leave a
    half-written services.json behind — the old file stands until the new
    one is complete.
    """
    directory = os.path.dirname(path) or '.'
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())

        # mkstemp makes the temp file 0600 and owned by this process. Renaming
        # it over the original would otherwise quietly drop the permissions and
        # ownership the data directory had, locking out backup scripts and
        # anyone reading a bind mount as another user.
        _carry_over_file_identity(path, tmp_path)

        try:
            os.replace(tmp_path, path)
        except OSError:
            # The destination can be a mount point of its own — someone may
            # bind-mount a single services.json — and replacing that fails.
            # Writing in place is not atomic, but it is what 1.0.0 did, and
            # it keeps those setups working.
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
            os.remove(tmp_path)

        if path == SERVICES_FILE:
            # The set of services changed, so the cached sweep is stale.
            _status_cache['checked_at'] = 0.0
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _carry_over_file_identity(original, replacement):
    """Give the replacement the mode, and where possible the owner, of the
    file it is about to stand in for."""
    try:
        existing = os.stat(original)
    except FileNotFoundError:
        os.chmod(replacement, 0o644)  # what a plain open(path, 'w') produced
        return

    os.chmod(replacement, stat.S_IMODE(existing.st_mode))
    try:
        os.chown(replacement, existing.st_uid, existing.st_gid)
    except (PermissionError, OSError):
        pass  # not running as root; the mode is the part that matters most


# Themes reference Tailwind and Inter by URL. Those are rewritten to local
# copies as the page is served, rather than in the theme files themselves,
# because user themes in /data/themes are frozen copies that no image update
# can reach. Rewriting here fixes those too, without editing anyone's file.
CDN_REWRITES = (
    (re.compile(r'https://cdn\.tailwindcss\.com[^"\']*'), '/static/vendor/tailwind.js'),
    (re.compile(r'https://fonts\.googleapis\.com/css2[^"\']*'), '/static/vendor/inter.css'),
)


def localise_assets(html):
    """Point a theme's external assets back at this server."""
    for pattern, replacement in CDN_REWRITES:
        html = pattern.sub(replacement, html)
    return html


def get_theme_html_path(theme_name):
    """Resolve theme HTML: user override first, then built-in."""
    user_path = os.path.join(USER_THEMES_DIR, f'{theme_name}.html')
    if os.path.exists(user_path):
        return user_path
    builtin_path = os.path.join(app.root_path, BUILTIN_THEMES_DIR, f'{theme_name}.html')
    if os.path.exists(builtin_path):
        return builtin_path
    return os.path.join(app.root_path, BUILTIN_THEMES_DIR, 'default.html')


# ── Routes ──

@app.route('/images/<path:filename>')
def serve_image(filename):
    # send_from_directory refuses paths that climb out of IMAGES_DIR;
    # joining the raw filename by hand served any file on the system.
    return send_from_directory(IMAGES_DIR, filename)


@app.route('/api/images', methods=['GET', 'POST'])
def handle_images():
    if request.method == 'POST':
        upload = request.files.get('file')
        if not upload or not upload.filename:
            return jsonify({"error": "No file provided"}), 400

        name = secure_filename(upload.filename)
        stem, ext = os.path.splitext(name)
        if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS or not stem:
            return jsonify({"error": "Unsupported image type"}), 400

        # Never clobber an icon another service may already point at.
        target = os.path.join(IMAGES_DIR, name)
        counter = 1
        while os.path.exists(target):
            name = f'{stem}-{counter}{ext}'
            target = os.path.join(IMAGES_DIR, name)
            counter += 1

        upload.save(target)
        return jsonify({"status": "success", "url": f'/images/{name}'}), 201

    images = [f'/images/{f}' for f in sorted(os.listdir(IMAGES_DIR))
              if os.path.splitext(f)[1].lower() in ALLOWED_IMAGE_EXTENSIONS]
    return jsonify(images)


@app.route('/')
def index():
    config = load_json(CONFIG_FILE)
    active_theme = config.get('theme', 'default')

    html_path = get_theme_html_path(active_theme)
    if not os.path.exists(html_path):
        html_path = get_theme_html_path('default')

    with open(html_path, 'r') as f:
        return localise_assets(f.read())


@app.route('/api/themes', methods=['GET', 'POST'])
def handle_themes():
    if request.method == 'POST':
        raw_name = request.json.get('name', '').strip()
        safe_name = re.sub(r'[^a-zA-Z0-9-]', '', raw_name).lower()
        if not safe_name:
            return jsonify({"error": "Invalid theme name"}), 400

        new_html_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.html')
        if not os.path.exists(new_html_path):
            # Clone the currently active theme's HTML
            config = load_json(CONFIG_FILE)
            current_theme = config.get('theme', 'default')
            source_html = get_theme_html_path(current_theme)
            shutil.copy2(source_html, new_html_path)

            config['theme'] = safe_name
            save_json(config, CONFIG_FILE)

        return jsonify({"status": "success", "theme": safe_name}), 201

    # List all available themes (built-in + user)
    themes = list(BUILTIN_THEMES)
    if os.path.exists(USER_THEMES_DIR):
        for f in os.listdir(USER_THEMES_DIR):
            if f.endswith('.html'):
                name = f.replace('.html', '')
                if name not in themes:
                    themes.append(name)
    return jsonify(themes)


@app.route('/api/themes/<theme_name>', methods=['GET', 'PUT', 'DELETE'])
def edit_theme_content(theme_name):
    safe_name = re.sub(r'[^a-zA-Z0-9-]', '', theme_name).lower()
    html_path = get_theme_html_path(safe_name)

    if not os.path.exists(html_path):
        return jsonify({"error": "Theme not found"}), 404

    if request.method == 'DELETE':
        if safe_name in BUILTIN_THEMES:
            # For built-in themes, only delete user override if it exists
            user_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.html')
            if os.path.exists(user_path):
                os.remove(user_path)
            else:
                return jsonify({"error": "Cannot delete a built-in theme."}), 403
        else:
            user_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.html')
            if os.path.exists(user_path):
                os.remove(user_path)

        config = load_json(CONFIG_FILE)
        if config.get('theme') == safe_name:
            config['theme'] = 'default'
            save_json(config, CONFIG_FILE)

        return jsonify({"status": "success"}), 200

    if request.method == 'PUT':
        content = request.json.get('content', '')
        # Always save to user themes dir so built-in files stay pristine
        save_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.html')
        with open(save_path, 'w') as f:
            f.write(content)
        return jsonify({"status": "success"}), 200

    # GET — return the theme's full HTML content
    with open(html_path, 'r') as f:
        return jsonify({"content": f.read()})


@app.route('/api/themes/<theme_name>/reset', methods=['POST'])
def reset_theme(theme_name):
    """Reset a theme back to the built-in version."""
    safe_name = re.sub(r'[^a-zA-Z0-9-]', '', theme_name).lower()
    user_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.html')
    if os.path.exists(user_path):
        os.remove(user_path)
    return jsonify({"status": "success"}), 200


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    config = load_json(CONFIG_FILE)
    if request.method == 'POST':
        config.update(request.json)
        save_json(config, CONFIG_FILE)
        return jsonify({"status": "success"}), 200
    return jsonify(config)


@app.route('/api/categories', methods=['GET', 'POST'])
def handle_categories():
    categories = load_json(CATEGORIES_FILE)
    if request.method == 'POST':
        new_cat = request.json.get('name')
        if new_cat and new_cat not in categories:
            categories.append(new_cat)
            save_json(categories, CATEGORIES_FILE)
        return jsonify({"status": "success"}), 201
    return jsonify(categories)


@app.route('/api/categories/<category_name>', methods=['PUT', 'DELETE'])
def modify_category(category_name):
    categories = load_json(CATEGORIES_FILE)
    services = load_json(SERVICES_FILE)

    if request.method == 'PUT':
        new_name = (request.json or {}).get('name', '').strip()
        if not new_name:
            return jsonify({"error": "Invalid category name"}), 400
        if category_name not in categories:
            return jsonify({"error": "Category not found"}), 404
        if new_name != category_name and new_name in categories:
            return jsonify({"error": "That category already exists"}), 409

        categories[categories.index(category_name)] = new_name
        save_json(categories, CATEGORIES_FILE)

        # Services point at their category by name, so they move with it.
        for service in services:
            if service.get('category') == category_name:
                service['category'] = new_name
        save_json(services, SERVICES_FILE)
        return jsonify({"status": "success", "name": new_name}), 200

    # DELETE — services may be moved somewhere rather than left orphaned.
    reassign_to = request.args.get('reassign')
    if reassign_to and reassign_to not in categories:
        return jsonify({"error": "Target category not found"}), 400

    if category_name in categories:
        categories.remove(category_name)
        save_json(categories, CATEGORIES_FILE)

    if reassign_to:
        for service in services:
            if service.get('category') == category_name:
                service['category'] = reassign_to
        save_json(services, SERVICES_FILE)

    return jsonify({"status": "success"}), 200


@app.route('/api/services', methods=['GET', 'POST'])
def handle_services():
    services = load_json(SERVICES_FILE)
    if request.method == 'POST':
        new_service = request.json
        new_service['id'] = str(uuid.uuid4())
        services.append(new_service)
        save_json(services, SERVICES_FILE)
        return jsonify({"status": "success"}), 201
    return jsonify(services)


@app.route('/api/services/reorder', methods=['POST'])
def reorder_services():
    """Stored order is display order, so reordering rewrites the list."""
    desired = (request.json or {}).get('order', [])
    services = load_json(SERVICES_FILE)
    by_id = {s.get('id'): s for s in services}

    ordered = [by_id.pop(sid) for sid in desired if sid in by_id]
    # Anything the client didn't mention keeps its relative order, at the back.
    ordered.extend(s for s in services if s.get('id') in by_id)

    save_json(ordered, SERVICES_FILE)
    return jsonify({"status": "success"}), 200


def check_service(service):
    """Report whether a service answers. A 4xx still counts as up — a 401 or
    a 404 means something is listening. A 5xx does not: behind a reverse
    proxy, a dead backend shows up as the proxy's 502/503/504."""
    url = (service.get('url') or '').strip()
    if not url:
        return 'down'
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    for method in ('HEAD', 'GET'):  # plenty of servers reject HEAD
        try:
            req = urllib.request.Request(
                url, method=method, headers={'User-Agent': 'dashboard-maker'})
            urllib.request.urlopen(
                req, timeout=STATUS_TIMEOUT_SECONDS, context=UNVERIFIED_SSL).close()
            return 'up'
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return 'up'
            # 5xx: try GET too, in case only HEAD is unimplemented (501).
        except Exception:
            continue
    return 'down'


@app.route('/api/status')
def service_status():
    now = time.time()
    if now - _status_cache['checked_at'] < STATUS_TTL_SECONDS:
        return jsonify(_status_cache['results'])

    services = load_json(SERVICES_FILE)
    if services:
        with ThreadPoolExecutor(max_workers=8) as pool:
            states = list(pool.map(check_service, services))
    else:
        states = []

    _status_cache['results'] = {s['id']: state
                                for s, state in zip(services, states) if s.get('id')}
    _status_cache['checked_at'] = now
    return jsonify(_status_cache['results'])


@app.route('/api/services/<service_id>', methods=['PUT', 'DELETE'])
def modify_service(service_id):
    services = load_json(SERVICES_FILE)

    if request.method == 'DELETE':
        services = [s for s in services if s.get('id') != service_id]
        save_json(services, SERVICES_FILE)
        return jsonify({"status": "success"}), 200

    updates = request.json or {}
    for service in services:
        if service.get('id') == service_id:
            service.update(updates)
            service['id'] = service_id  # the id is ours to set, never the client's
            save_json(services, SERVICES_FILE)
            return jsonify({"status": "success"}), 200

    return jsonify({"error": "Service not found"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
