import json
import os
import uuid
import re
import shutil
from flask import Flask, request, jsonify, render_template, send_file

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
USER_HTML_FILE = os.path.join(DATA_DIR, 'custom_base.html')
BUILTIN_HTML = os.path.join('templates', 'base.html')

# ── Theme configurations (text/labels per theme) ──

THEME_CONFIGS = {
    'default': {
        'title': 'Home Server Dashboard',
        'title_html': 'System <span class="title-bold">Dashboard</span>',
        'icon_svg': '<rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>'
                    '<rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>'
                    '<line x1="6" y1="6" x2="6.01" y2="6"></line>'
                    '<line x1="6" y1="18" x2="6.01" y2="18"></line>',
        'edit_label': 'Edit',
        'edit_active_label': 'Editing',
        'add_service_label': '+ Add Service',
        'add_category_label': '+ Add Category',
        'clone_theme_label': '+ Clone Theme',
        'edit_code_label': '</> Edit Current Theme',
        'delete_theme_label': '- Delete Theme',
        'editor_heading': 'Raw HTML / CSS Editor',
        'editor_warning': 'Warning: Editing this directly changes your UI!',
        'save_service_text': 'Save to Dashboard',
        'save_compile_text': 'Save & Compile Theme',
        'discard_text': 'Discard Changes',
        'show_labels': False,
        'name_placeholder': 'Name',
        'desc_label': 'INFO',
        'desc_placeholder': 'Description',
        'url_label': 'URL',
        'url_placeholder': 'URL',
        'category_label': 'GROUP',
        'select_category_text': 'Select Category...',
        'panel_heading_service': None,
        'footer_left': 'Local Network',
        'footer_right': 'All Systems Operational',
        'footer_dot': False,
        'footer_status_dot': False,
    },
    'neon': {
        'title': 'Home Server Dashboard',
        'title_html': 'SYSTEM <span class="title-bold">CORE</span>',
        'icon_svg': '<rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>'
                    '<rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>'
                    '<line x1="6" y1="6" x2="6.01" y2="6"></line>'
                    '<line x1="6" y1="18" x2="6.01" y2="18"></line>',
        'edit_label': 'EDIT',
        'edit_active_label': 'ACTIVE',
        'add_service_label': '[ + ] INITIALIZE_SERVICE',
        'add_category_label': '[ + ] CREATE_GROUP',
        'clone_theme_label': '[ + ] CLONE_THEME',
        'edit_code_label': '</> EDIT_SOURCE_CODE',
        'delete_theme_label': '[ - ] PURGE_THEME',
        'editor_heading': 'RAW HTML OVERRIDE',
        'editor_warning': 'WARNING: CORE SYSTEM OVERRIDE',
        'save_service_text': 'Deploy Service',
        'save_compile_text': 'COMPILE_AND_SAVE',
        'discard_text': 'ABORT',
        'show_labels': True,
        'name_placeholder': 'Plex',
        'desc_label': 'INFO',
        'desc_placeholder': 'Media Server',
        'url_label': 'ADDRESS',
        'url_placeholder': '192.168.1.50',
        'category_label': 'GROUP',
        'select_category_text': 'Select Group...',
        'panel_heading_service': None,
        'footer_left': '// LOCAL_NET_ESTABLISHED',
        'footer_right': 'STATUS: OPTIMAL',
        'footer_dot': False,
        'footer_status_dot': True,
    },
    'ocean': {
        'title': 'Ocean Server Dashboard',
        'title_html': 'System <span class="title-bold">Dashboard</span>',
        'icon_svg': '<path d="M12 2L2 7l10 5 10-5-10-5z"></path>'
                    '<path d="M2 17l10 5 10-5"></path>'
                    '<path d="M2 12l10 5 10-5"></path>',
        'edit_label': 'Edit UI',
        'edit_active_label': 'Lock UI',
        'add_service_label': '+ Add Service',
        'add_category_label': '+ Add Category',
        'clone_theme_label': '+ Clone Theme',
        'edit_code_label': '</> Edit Theme Code',
        'delete_theme_label': '- Delete Theme',
        'editor_heading': 'Theme CSS Editor',
        'editor_warning': 'Changes apply immediately on save',
        'save_service_text': 'Save Service',
        'save_compile_text': 'Save & Compile',
        'discard_text': 'Discard Changes',
        'show_labels': True,
        'name_placeholder': 'Name',
        'desc_label': 'DESCRIPTION',
        'desc_placeholder': 'Description',
        'url_label': 'URL',
        'url_placeholder': 'URL',
        'category_label': 'CATEGORY',
        'select_category_text': 'Select Category...',
        'panel_heading_service': 'Deploy New Service',
        'footer_left': 'Local Subnet',
        'footer_right': 'All Systems Hydrated',
        'footer_dot': True,
        'footer_status_dot': False,
    },
}


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


def get_theme_config(theme_name):
    """Get the config dict for a theme, falling back to default."""
    return THEME_CONFIGS.get(theme_name, THEME_CONFIGS['default'])


def get_theme_css_path(theme_name):
    """Resolve theme CSS: user override first, then built-in."""
    user_path = os.path.join(USER_THEMES_DIR, f'{theme_name}.css')
    if os.path.exists(user_path):
        return user_path
    builtin_path = os.path.join(app.static_folder, 'css', 'themes', f'{theme_name}.css')
    if os.path.exists(builtin_path):
        return builtin_path
    return os.path.join(app.static_folder, 'css', 'themes', 'default.css')


# ── Routes ──

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_file(os.path.join(IMAGES_DIR, filename))


@app.route('/theme-css/<theme_name>.css')
def serve_theme_css(theme_name):
    safe_name = re.sub(r'[^a-zA-Z0-9-]', '', theme_name).lower()
    css_path = get_theme_css_path(safe_name)
    return send_file(css_path, mimetype='text/css')


@app.route('/')
def index():
    config = load_json(CONFIG_FILE)
    active_theme = config.get('theme', 'default')

    # Verify the theme has a CSS file
    css_path = get_theme_css_path(active_theme)
    if not os.path.exists(css_path):
        active_theme = 'default'

    tc = get_theme_config(active_theme)

    # Use custom HTML template if it exists
    if os.path.exists(USER_HTML_FILE):
        from jinja2 import Template
        with open(USER_HTML_FILE, 'r') as f:
            template_str = f.read()
        template = Template(template_str)
        return template.render(active_theme=active_theme, **tc)

    return render_template('base.html', active_theme=active_theme, **tc)


@app.route('/api/html', methods=['GET', 'PUT'])
def handle_html():
    if request.method == 'PUT':
        content = request.json.get('content', '')
        with open(USER_HTML_FILE, 'w') as f:
            f.write(content)
        return jsonify({"status": "success"}), 200

    # GET — return custom HTML if exists, else the built-in template
    if os.path.exists(USER_HTML_FILE):
        with open(USER_HTML_FILE, 'r') as f:
            return jsonify({"content": f.read(), "is_custom": True})
    else:
        builtin_path = os.path.join(app.root_path, BUILTIN_HTML)
        with open(builtin_path, 'r') as f:
            return jsonify({"content": f.read(), "is_custom": False})


@app.route('/api/html/reset', methods=['POST'])
def reset_html():
    """Reset HTML back to the built-in template."""
    if os.path.exists(USER_HTML_FILE):
        os.remove(USER_HTML_FILE)
    return jsonify({"status": "success"}), 200


@app.route('/api/themes', methods=['GET', 'POST'])
def handle_themes():
    if request.method == 'POST':
        raw_name = request.json.get('name', '').strip()
        safe_name = re.sub(r'[^a-zA-Z0-9-]', '', raw_name).lower()
        if not safe_name:
            return jsonify({"error": "Invalid theme name"}), 400

        new_css_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.css')
        if not os.path.exists(new_css_path):
            # Clone the currently active theme's CSS
            config = load_json(CONFIG_FILE)
            current_theme = config.get('theme', 'default')
            source_css = get_theme_css_path(current_theme)
            shutil.copy2(source_css, new_css_path)

            config['theme'] = safe_name
            save_json(config, CONFIG_FILE)

        return jsonify({"status": "success", "theme": safe_name}), 201

    # List all available themes (built-in + user)
    themes = list(BUILTIN_THEMES)
    if os.path.exists(USER_THEMES_DIR):
        for f in os.listdir(USER_THEMES_DIR):
            if f.endswith('.css'):
                name = f.replace('.css', '')
                if name not in themes:
                    themes.append(name)
    return jsonify(themes)


@app.route('/api/themes/<theme_name>', methods=['GET', 'PUT', 'DELETE'])
def edit_theme_content(theme_name):
    safe_name = re.sub(r'[^a-zA-Z0-9-]', '', theme_name).lower()
    css_path = get_theme_css_path(safe_name)

    if not os.path.exists(css_path):
        return jsonify({"error": "Theme not found"}), 404

    if request.method == 'DELETE':
        if safe_name in BUILTIN_THEMES:
            # For built-in themes, only delete user override if it exists
            user_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.css')
            if os.path.exists(user_path):
                os.remove(user_path)
            else:
                return jsonify({"error": "Cannot delete a built-in theme."}), 403
        else:
            user_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.css')
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
        save_path = os.path.join(USER_THEMES_DIR, f'{safe_name}.css')
        with open(save_path, 'w') as f:
            f.write(content)
        return jsonify({"status": "success"}), 200

    # GET
    with open(css_path, 'r') as f:
        return jsonify({"content": f.read()})


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
