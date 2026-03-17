import json
import os
import uuid
import re
import shutil
from flask import Flask, request, jsonify, send_file

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
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


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
    return send_file(os.path.join(IMAGES_DIR, filename))


@app.route('/')
def index():
    config = load_json(CONFIG_FILE)
    active_theme = config.get('theme', 'default')

    html_path = get_theme_html_path(active_theme)
    if not os.path.exists(html_path):
        html_path = get_theme_html_path('default')

    with open(html_path, 'r') as f:
        return f.read()


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


@app.route('/api/categories/<category_name>', methods=['DELETE'])
def delete_category(category_name):
    categories = load_json(CATEGORIES_FILE)
    if category_name in categories:
        categories.remove(category_name)
        save_json(categories, CATEGORIES_FILE)
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


@app.route('/api/services/<service_id>', methods=['DELETE'])
def delete_service(service_id):
    services = load_json(SERVICES_FILE)
    services = [s for s in services if s.get('id') != service_id]
    save_json(services, SERVICES_FILE)
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
