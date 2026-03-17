import json
import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')

app.config['TEMPLATES_AUTO_RELOAD'] = True

DATA_DIR = '/data'
IMAGES_DIR = '/images'

SERVICES_FILE = os.path.join(DATA_DIR, 'services.json')
CATEGORIES_FILE = os.path.join(DATA_DIR, 'categories.json')
USER_HTML_FILE = os.path.join(DATA_DIR, 'custom_base.html')
BUILTIN_HTML = os.path.join('templates', 'base.html')

DEFAULT_CATEGORIES = ["Media & Content", "Management & Network", "Ai & Generation"]


# ── Setup ──

def setup_environment():
    for d in [DATA_DIR, IMAGES_DIR]:
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(SERVICES_FILE):
        with open(SERVICES_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'w') as f:
            json.dump(DEFAULT_CATEGORIES, f)


setup_environment()


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


# ── Routes ──

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_file(os.path.join(IMAGES_DIR, filename))


@app.route('/')
def index():
    # Use custom HTML if it exists, otherwise the built-in template
    if os.path.exists(USER_HTML_FILE):
        with open(USER_HTML_FILE, 'r') as f:
            return f.read()

    return render_template('base.html', title='Dashboard')


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
