import json
import os
import uuid
import re
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, 
            template_folder='/templates', 
            static_folder='/images', 
            static_url_path='/images')

app.config['TEMPLATES_AUTO_RELOAD'] = True

DATA_DIR = '/data'
IMAGES_DIR = '/images'
TEMPLATES_DIR = '/templates'

SERVICES_FILE = os.path.join(DATA_DIR, 'services.json')
CATEGORIES_FILE = os.path.join(DATA_DIR, 'categories.json')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

DEFAULT_CATEGORIES = ["Media & Content", "Management & Network", "Ai & Generation"]
DEFAULT_CONFIG = {"theme": "ocean"}

# ---------------------------------------------------------------------------
# DEFAULT THEME HTML 
# ---------------------------------------------------------------------------
DEFAULT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Server Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0a0a0a; color: #e5e5e5; font-family: 'Inter', system-ui, sans-serif; }
        .service-card { background: #171717; border: 1px solid #262626; transition: all 0.2s ease-in-out; }
        .service-card:hover { background: #1f1f1f; border-color: #404040; transform: translateY(-2px); }
        .section-title { color: #737373; letter-spacing: 0.05em; text-transform: uppercase; font-size: 0.75rem; font-weight: 700; }
        
        details > summary { list-style: none; }
        details > summary::-webkit-details-marker { display: none; }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0a0a0a; }
        ::-webkit-scrollbar-thumb { background: #262626; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #404040; }

        @keyframes dropFade {
            0% { opacity: 0; transform: translateY(-8px) scale(0.98); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-drop-fade {
            animation: dropFade 0.2s ease-out both;
            transform-origin: top;
        }
        
        #theme-code-editor { tab-size: 4; }

        /* EDIT MODE CSS MAGIC & ANIMATIONS */
        body { border-top: 3px solid transparent; transition: border-color 0.3s ease; }
        body.edit-mode { border-top-color: #333; }
        
        body:not(.edit-mode) .edit-mode-only { display: none !important; }
        body.edit-mode .edit-mode-only {
            animation: editFadeIn 0.3s ease-out both;
        }
        @keyframes editFadeIn {
            0% { opacity: 0; transform: translateY(-10px); }
            100% { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body class="p-6 md:p-16">
    <div class="max-w-5xl mx-auto">
        <header class="mb-12 flex items-center justify-between">
            <div class="flex items-center gap-6">
                <svg class="h-12 w-12 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                    <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                    <line x1="6" y1="6" x2="6.01" y2="6"></line>
                    <line x1="6" y1="18" x2="6.01" y2="18"></line>
                </svg>
                <div>
                    <h1 class="text-2xl font-light tracking-tight text-white">System <span class="font-bold">Dashboard</span></h1>
                    <div class="h-1 w-12 bg-white mt-2"></div>
                </div>
            </div>
            
            <div class="flex items-center gap-4">
                <button id="edit-mode-btn" onclick="toggleEditMode()" class="flex items-center gap-2 bg-[#1a1a1a] text-neutral-400 border border-[#333] py-2 px-4 rounded text-xs focus:outline-none transition uppercase tracking-wider font-bold hover:bg-[#262626] hover:text-white">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                    <span>Edit</span>
                </button>

                <div class="relative inline-block text-left">
                    <button type="button" onclick="toggleDropdown('theme-dropdown', event)" class="flex items-center gap-2 bg-[#1a1a1a] text-neutral-400 border border-[#333] py-2 pl-4 pr-3 rounded text-xs focus:border-white outline-none transition uppercase tracking-wider font-bold hover:bg-[#262626]">
                        <span id="theme-selected-text">DEFAULT THEME</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                    <div id="theme-dropdown" class="hidden animate-drop-fade origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-xl bg-[#1a1a1a] border border-[#333] z-50 overflow-hidden">
                        <div class="py-1" id="theme-options"></div>
                    </div>
                    <input type="hidden" id="theme-selector" value="default">
                </div>
            </div>
        </header>

        <div class="flex flex-wrap gap-4 mb-16 relative edit-mode-only">
            <details class="group" id="details-service">
                <summary class="cursor-pointer text-xs font-bold text-neutral-500 uppercase tracking-widest hover:text-white transition inline-block px-2">
                    + Add Service
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#111] border border-[#262626] rounded-lg shadow-2xl absolute z-40 w-full max-w-4xl left-0">
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <input type="text" id="name" placeholder="Name" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full">
                        <input type="text" id="desc" placeholder="Description" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full">
                        <input type="text" id="url" placeholder="URL" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full">
                        <div class="relative w-full">
                            <button type="button" onclick="toggleDropdown('category-dropdown', event)" class="flex justify-between items-center bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full hover:bg-[#262626]">
                                <span id="category-selected-text" class="truncate">Select Category...</span>
                                <svg class="w-4 h-4 text-neutral-400 ml-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </button>
                            <div id="category-dropdown" class="hidden animate-drop-fade absolute z-50 w-full mt-1 rounded-md shadow-xl bg-[#1a1a1a] border border-[#333] max-h-48 overflow-y-auto">
                                <div class="py-1" id="category-options"></div>
                            </div>
                            <input type="hidden" id="category" value="">
                        </div>
                    </div>
                    <button onclick="addService()" class="mt-6 bg-white text-black px-6 py-2.5 rounded text-sm font-semibold hover:bg-gray-200 transition">Save to Dashboard</button>
                </div>
            </details>

            <details class="group" id="details-category">
                <summary class="cursor-pointer text-xs font-bold text-neutral-500 uppercase tracking-widest hover:text-white transition inline-block px-2">
                    + Add Category
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#111] border border-[#262626] rounded-lg shadow-2xl absolute z-40 w-full max-w-md left-0 sm:left-auto">
                    <div class="flex gap-4">
                        <input type="text" id="new-category-name" placeholder="Category Name" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full flex-1">
                        <button onclick="addCategory()" class="bg-white text-black px-4 py-2.5 rounded text-sm font-semibold hover:bg-gray-200 transition">Add</button>
                    </div>
                </div>
            </details>
            
            <details class="group" id="details-theme-clone">
                <summary class="cursor-pointer text-xs font-bold text-neutral-500 uppercase tracking-widest hover:text-white transition inline-block px-2">
                    + Clone Theme
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#111] border border-[#262626] rounded-lg shadow-2xl absolute z-40 w-full max-w-md left-0 sm:left-auto">
                    <div class="flex gap-4">
                        <input type="text" id="new-theme-name" placeholder="New Theme Name (e.g. Ocean)" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full flex-1">
                        <button onclick="cloneTheme()" class="bg-white text-black px-4 py-2.5 rounded text-sm font-semibold hover:bg-gray-200 transition">Clone</button>
                    </div>
                </div>
            </details>

            <details class="group" id="details-theme-edit">
                <summary class="cursor-pointer text-xs font-bold text-indigo-400 uppercase tracking-widest hover:text-indigo-300 transition inline-block px-2">
                    &lt;/&gt; Edit Current Theme
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#111] border border-[#262626] rounded-lg shadow-2xl absolute z-50 w-full left-0 right-0">
                    <div class="flex justify-between items-center mb-4">
                        <span class="text-xs font-bold text-neutral-400 uppercase tracking-widest">Raw HTML / Tailwind CSS Editor</span>
                        <span class="text-xs text-yellow-500">Warning: Editing this directly changes your UI!</span>
                    </div>
                    <textarea id="theme-code-editor" class="w-full h-[500px] bg-[#0a0a0a] text-green-400 font-mono text-xs p-4 border border-[#333] rounded outline-none focus:border-indigo-500 transition" spellcheck="false"></textarea>
                    <div class="mt-4 flex gap-4">
                        <button onclick="saveThemeCode(event)" class="bg-indigo-600 text-white px-6 py-2.5 rounded text-sm font-bold hover:bg-indigo-500 transition">Save & Compile Theme</button>
                        <button onclick="loadThemeCode()" class="text-neutral-500 hover:text-white text-sm transition">Discard Changes</button>
                    </div>
                </div>
            </details>

            <button onclick="deleteCurrentTheme()" class="cursor-pointer text-xs font-bold text-red-500 uppercase tracking-widest hover:text-red-400 transition inline-block px-2">
                - Delete Theme
            </button>
        </div>

        <div id="dynamic-content"></div>

        <footer class="mt-24 pt-8 border-t border-neutral-900 flex justify-between items-center text-neutral-600 text-xs tracking-widest uppercase">
            <span>Local Network</span>
            <span>All Systems Operational</span>
        </footer>
    </div>

    <script>
        let globalCategories = [];
        const detailsService = document.getElementById('details-service');
        const detailsCategory = document.getElementById('details-category');
        const detailsThemeClone = document.getElementById('details-theme-clone');
        const detailsThemeEdit = document.getElementById('details-theme-edit');

        const allDetails = [detailsService, detailsCategory, detailsThemeClone, detailsThemeEdit];
        allDetails.forEach(detail => {
            detail.addEventListener('toggle', () => {
                if (detail.open) {
                    allDetails.forEach(other => { if (other !== detail) other.removeAttribute('open'); });
                    
                    const animatedChild = detail.querySelector('.animate-drop-fade');
                    if(animatedChild) {
                        animatedChild.classList.remove('animate-drop-fade');
                        void animatedChild.offsetWidth; // force reflow
                        animatedChild.classList.add('animate-drop-fade');
                    }
                    if (detail === detailsThemeEdit) loadThemeCode(); 
                }
            });
        });

        function toggleEditMode() {
            document.body.classList.toggle('edit-mode');
            const btn = document.getElementById('edit-mode-btn');
            
            if(document.body.classList.contains('edit-mode')) {
                btn.classList.add('text-black', 'bg-white', 'border-white');
                btn.classList.remove('text-neutral-400', 'bg-[#1a1a1a]', 'border-[#333]');
            } else {
                btn.classList.remove('text-black', 'bg-white', 'border-white');
                btn.classList.add('text-neutral-400', 'bg-[#1a1a1a]', 'border-[#333]');
                allDetails.forEach(d => d.removeAttribute('open'));
            }
        }
        
        function toggleDropdown(id, event) {
            event.stopPropagation();
            const dropdown = document.getElementById(id);
            document.querySelectorAll('[id$="-dropdown"]').forEach(d => {
                if (d.id !== id) d.classList.add('hidden');
            });

            if (dropdown.classList.contains('hidden')) {
                dropdown.classList.remove('hidden');
                dropdown.classList.remove('animate-drop-fade');
                void dropdown.offsetWidth;
                dropdown.classList.add('animate-drop-fade');
            } else {
                dropdown.classList.add('hidden');
            }
        }

        document.addEventListener('click', () => {
            document.querySelectorAll('[id$="-dropdown"]').forEach(d => d.classList.add('hidden'));
        });

        async function init() { 
            await fetchThemes(); await fetchCategories(); await fetchServices(); 
        }

        async function fetchThemes() {
            const [themesRes, configRes] = await Promise.all([ fetch('/api/themes'), fetch('/api/config') ]);
            const themes = await themesRes.json();
            const config = await configRes.json();
            
            document.getElementById('theme-selected-text').textContent = config.theme + ' THEME';
            document.getElementById('theme-selector').value = config.theme;

            const optionsContainer = document.getElementById('theme-options');
            optionsContainer.innerHTML = '';
            themes.forEach(t => {
                const a = document.createElement('a');
                a.href = '#';
                a.className = 'block px-4 py-3 text-xs text-neutral-300 hover:bg-[#262626] hover:text-white uppercase font-bold tracking-wider transition';
                a.textContent = t + ' Theme';
                a.onclick = (e) => { e.preventDefault(); changeTheme(t); };
                optionsContainer.appendChild(a);
            });
        }

        function changeTheme(newTheme) {
            fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme: newTheme }) })
            .then(() => location.reload()); 
        }

        function cloneTheme() {
            const nameInput = document.getElementById('new-theme-name');
            const val = nameInput.value.trim();
            if (!val) return;
            fetch('/api/themes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: val }) })
            .then(() => location.reload()); 
        }

        function deleteCurrentTheme() {
            const currentTheme = document.getElementById('theme-selector').value;
            if (currentTheme === 'default') { alert("The default theme cannot be deleted."); return; }
            if (confirm(`Are you sure you want to delete the '${currentTheme}' theme?`)) {
                fetch(`/api/themes/${currentTheme}`, { method: 'DELETE' }).then(res => {
                    if (res.ok) { location.reload(); } else { res.json().then(data => alert(data.error)); }
                });
            }
        }

        async function loadThemeCode() {
            const currentTheme = document.getElementById('theme-selector').value;
            const res = await fetch(`/api/themes/${currentTheme}`);
            const data = await res.json();
            document.getElementById('theme-code-editor').value = data.content;
        }

        async function saveThemeCode(event) {
            const currentTheme = document.getElementById('theme-selector').value;
            const content = document.getElementById('theme-code-editor').value;
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = "Saving...";
            
            try {
                const response = await fetch(`/api/themes/${currentTheme}`, {
                    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content })
                });
                if (!response.ok) throw new Error(`Server returned ${response.status}`);
                location.reload(); 
            } catch (error) {
                alert(`Failed to save theme!`);
                btn.innerText = originalText;
            }
        }

        async function fetchCategories() {
            const res = await fetch('/api/categories');
            globalCategories = await res.json();
            const optionsContainer = document.getElementById('category-options');
            optionsContainer.innerHTML = '';
            if(globalCategories.length > 0) {
                document.getElementById('category-selected-text').textContent = globalCategories[0];
                document.getElementById('category').value = globalCategories[0];
            }
            globalCategories.forEach(cat => {
                const a = document.createElement('a'); a.href = '#';
                a.className = 'block px-4 py-2.5 text-sm text-white hover:bg-[#262626] transition';
                a.textContent = cat;
                a.onclick = (e) => {
                    e.preventDefault();
                    document.getElementById('category-selected-text').textContent = cat;
                    document.getElementById('category').value = cat;
                };
                optionsContainer.appendChild(a);
            });
        }

        async function fetchServices() {
            const res = await fetch('/api/services');
            const services = await res.json();
            renderDashboard(services);
        }

        function renderDashboard(services) {
            const container = document.getElementById('dynamic-content');
            container.innerHTML = '';
            const grouped = {};
            globalCategories.forEach(cat => grouped[cat] = []); 
            services.forEach(srv => {
                if (grouped[srv.category] !== undefined) { grouped[srv.category].push(srv); } 
                else { if (!grouped['Other']) grouped['Other'] = []; grouped['Other'].push(srv); }
            });

            for (const [category, items] of Object.entries(grouped)) {
                if (items.length === 0) continue;
                const section = document.createElement('section');
                section.className = 'mb-16';
                const title = document.createElement('h2');
                title.className = 'section-title mb-6 flex justify-between items-center group/cat';
                title.innerHTML = `<span>${category}</span><button onclick="deleteCategory('${category}')" class="edit-mode-only text-neutral-700 hover:text-red-500 opacity-0 group-hover/cat:opacity-100 transition text-xs font-normal lowercase tracking-normal">remove</button>`;
                section.appendChild(title);

                const grid = document.createElement('div');
                grid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4';

                items.forEach(srv => {
                    let link = srv.url; if (link && !link.startsWith('http')) link = 'http://' + link;
                    const a = document.createElement('a');
                    a.href = link; a.target = '_blank';
                    a.className = 'service-card p-5 rounded-lg block relative group/card';
                    a.innerHTML = `
                        <div class="text-white font-medium">${srv.name}</div>
                        <div class="text-xs text-neutral-500 mt-1">${srv.desc || ''}</div>
                        <button onclick="deleteService(event, '${srv.id}')" class="edit-mode-only absolute top-4 right-4 text-neutral-600 hover:text-red-500 opacity-0 group-hover/card:opacity-100 transition-opacity">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        </button>`;
                    grid.appendChild(a);
                });
                section.appendChild(grid);
                container.appendChild(section);
            }
        }

        function addCategory() {
            const val = document.getElementById('new-category-name').value.trim();
            if (!val) return;
            fetch('/api/categories', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: val }) }).then(() => location.reload());
        }
        function deleteCategory(catName) {
            if(confirm(`Remove '${catName}'?`)) fetch(`/api/categories/${encodeURIComponent(catName)}`, { method: 'DELETE' }).then(() => location.reload());
        }
        function addService() {
            const newService = {
                name: document.getElementById('name').value, desc: document.getElementById('desc').value,
                url: document.getElementById('url').value, category: document.getElementById('category').value
            };
            fetch('/api/services', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newService) }).then(() => location.reload());
        }
        function deleteService(event, id) {
            event.preventDefault(); 
            if(confirm('Remove service?')) fetch(`/api/services/${id}`, { method: 'DELETE' }).then(() => location.reload()); 
        }
        init();
    </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# NEON THEME HTML 
# ---------------------------------------------------------------------------
NEON_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Server Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <style>
        :root { --neon-cyan: #00f3ff; --neon-pink: #ff00a0; --bg-deep: #06040d; --glass: rgba(15, 5, 30, 0.85); }
        body { background-color: var(--bg-deep); background-image: radial-gradient(circle at 50% 0%, #1c0936 0%, transparent 50%), linear-gradient(rgba(18, 16, 33, 0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(18, 16, 33, 0.3) 1px, transparent 1px); background-size: 100% 100%, 30px 30px, 30px 30px; color: #e5e5e5; font-family: 'Inter', system-ui, sans-serif; min-height: 100vh; }
        .service-card { background: rgba(20, 10, 40, 0.5); backdrop-filter: blur(8px); border: 1px solid #3b1b63; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .service-card:hover { background: rgba(30, 15, 60, 0.7); border-color: var(--neon-cyan); box-shadow: 0 0 20px rgba(0, 243, 255, 0.2), inset 0 0 10px rgba(0, 243, 255, 0.1); transform: translateY(-4px); }
        .section-title { color: var(--neon-pink); letter-spacing: 0.15em; text-transform: uppercase; font-size: 0.75rem; font-weight: 800; text-shadow: 0 0 8px rgba(255, 0, 160, 0.4); }
        .neon-input { background: rgba(10, 5, 20, 0.8) !important; border: 1px solid #3b1b63 !important; color: var(--neon-cyan) !important; }
        .neon-input:focus { border-color: var(--neon-cyan) !important; box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); outline: none; }
        .neon-dropdown { background: var(--glass) !important; border: 1px solid var(--neon-cyan) !important; backdrop-filter: blur(12px); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 243, 255, 0.1); }
        .neon-btn-primary { background: var(--neon-cyan); color: #000; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; box-shadow: 0 0 15px rgba(0, 243, 255, 0.4); transition: all 0.2s; }
        .neon-btn-primary:hover { background: #fff; box-shadow: 0 0 25px var(--neon-cyan); }
        details > summary { list-style: none; }
        details > summary::-webkit-details-marker { display: none; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-deep); }
        ::-webkit-scrollbar-thumb { background: #3b1b63; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--neon-pink); }
        
        @keyframes dropFade { 0% { opacity: 0; transform: translateY(-12px) scale(0.95); filter: blur(4px); } 100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); } }
        .animate-drop-fade { animation: dropFade 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) both; transform-origin: top; }
        
        #theme-code-editor { tab-size: 4; }

        /* EDIT MODE CSS MAGIC & ANIMATIONS */
        body { border-top: 3px solid transparent; transition: border-color 0.4s ease; }
        body.edit-mode { border-top-color: var(--neon-pink); }
        
        body:not(.edit-mode) .edit-mode-only { display: none !important; }
        body.edit-mode .edit-mode-only {
            animation: editFadeIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
        }
        @keyframes editFadeIn {
            0% { opacity: 0; transform: translateY(-15px) scale(0.98); filter: blur(4px); }
            100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }
    </style>
</head>
<body class="p-6 md:p-16">
    <div class="max-w-5xl mx-auto">
        <header class="mb-16 flex items-center justify-between">
            <div class="flex items-center gap-6">
                <svg class="h-12 w-12 text-[#ff00a0] drop-shadow-[0_0_8px_rgba(255,0,160,0.6)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                    <line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line>
                </svg>
                <div>
                    <h1 class="text-2xl font-light tracking-tighter text-white">SYSTEM <span class="font-black text-[#00f3ff]">CORE</span></h1>
                    <div class="h-0.5 w-12 bg-[#ff00a0] mt-1 shadow-[0_0_10px_#ff00a0]"></div>
                </div>
            </div>
            
            <div class="flex items-center gap-4">
                <button id="edit-mode-btn" onclick="toggleEditMode()" class="flex items-center gap-2 bg-[#1a1a1a]/50 border border-[#3b1b63] text-indigo-400 py-2.5 px-4 rounded text-[10px] focus:outline-none transition-all uppercase tracking-[0.2em] font-black hover:bg-[#262626] hover:text-[#00f3ff]">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                    <span>EDIT</span>
                </button>

                <div class="relative inline-block text-left">
                    <button type="button" onclick="toggleDropdown('theme-dropdown', event)" class="flex items-center gap-3 bg-[#1a1a1a]/50 border border-[#3b1b63] text-[#00f3ff] py-2.5 px-4 rounded text-[10px] focus:border-[#00f3ff] outline-none transition-all uppercase tracking-[0.2em] font-black hover:bg-[#262626]">
                        <span id="theme-selected-text">LOADING...</span>
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                    <div id="theme-dropdown" class="hidden animate-drop-fade origin-top-right absolute right-0 mt-2 w-56 rounded shadow-2xl neon-dropdown z-50 overflow-hidden">
                        <div class="py-1" id="theme-options"></div>
                    </div>
                    <input type="hidden" id="theme-selector" value="default">
                </div>
            </div>
        </header>

        <div class="flex flex-wrap gap-4 mb-20 relative edit-mode-only">
            <details class="group" id="details-service">
                <summary class="cursor-pointer text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] hover:text-[#00f3ff] transition inline-block px-2">
                    [ + ] INITIALIZE_SERVICE
                </summary>
                <div class="animate-drop-fade mt-6 p-8 rounded-lg shadow-2xl absolute z-40 w-full max-w-4xl left-0 border border-[#ff00a0] bg-[#0f051e]/95 backdrop-blur-xl">
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div class="space-y-1"><label class="text-[9px] font-bold text-indigo-400 ml-1">NAME</label><input type="text" id="name" placeholder="Plex" class="neon-input p-3 rounded text-sm w-full"></div>
                        <div class="space-y-1"><label class="text-[9px] font-bold text-indigo-400 ml-1">INFO</label><input type="text" id="desc" placeholder="Media Server" class="neon-input p-3 rounded text-sm w-full"></div>
                        <div class="space-y-1"><label class="text-[9px] font-bold text-indigo-400 ml-1">ADDRESS</label><input type="text" id="url" placeholder="192.168.1.50" class="neon-input p-3 rounded text-sm w-full"></div>
                        <div class="space-y-1">
                            <label class="text-[9px] font-bold text-indigo-400 ml-1">GROUP</label>
                            <div class="relative w-full">
                                <button type="button" onclick="toggleDropdown('category-dropdown', event)" class="flex justify-between items-center neon-input p-3 rounded text-sm w-full hover:bg-white/5 transition-all">
                                    <span id="category-selected-text" class="truncate">Select Group...</span><svg class="w-4 h-4 text-indigo-400 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                </button>
                                <div id="category-dropdown" class="hidden animate-drop-fade absolute z-50 w-full mt-2 rounded-md neon-dropdown max-h-48 overflow-y-auto"><div class="py-1" id="category-options"></div></div>
                                <input type="hidden" id="category" value="">
                            </div>
                        </div>
                    </div>
                    <button onclick="addService()" class="mt-8 px-8 py-3 rounded text-xs neon-btn-primary">Deploy Service</button>
                </div>
            </details>

            <details class="group" id="details-category">
                <summary class="cursor-pointer text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] hover:text-[#ff00a0] transition inline-block px-2">
                    [ + ] CREATE_GROUP
                </summary>
                <div class="animate-drop-fade mt-6 p-8 rounded-lg shadow-2xl absolute z-40 w-full max-w-md left-0 sm:left-auto border border-[#ff00a0] bg-[#0f051e]/95 backdrop-blur-xl">
                    <div class="flex gap-4 items-end">
                        <div class="flex-1 space-y-1">
                            <label class="text-[9px] font-bold text-indigo-400 ml-1">GROUP_NAME</label><input type="text" id="new-category-name" class="neon-input p-3 rounded text-sm w-full">
                        </div>
                        <button onclick="addCategory()" class="px-6 py-3 rounded text-xs neon-btn-primary">ADD</button>
                    </div>
                </div>
            </details>
            
            <details class="group" id="details-theme-clone">
                <summary class="cursor-pointer text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] hover:text-[#ff00a0] transition inline-block px-2">
                    [ + ] CLONE_THEME
                </summary>
                <div class="animate-drop-fade mt-6 p-8 rounded-lg shadow-2xl absolute z-40 w-full max-w-md left-0 sm:left-auto border border-[#ff00a0] bg-[#0f051e]/95 backdrop-blur-xl">
                    <div class="flex gap-4 items-end">
                        <div class="flex-1 space-y-1">
                            <label class="text-[9px] font-bold text-indigo-400 ml-1">THEME_ID</label><input type="text" id="new-theme-name" placeholder="E.G. OCEAN" class="neon-input p-3 rounded text-sm w-full">
                        </div>
                        <button onclick="cloneTheme()" class="px-6 py-3 rounded text-xs neon-btn-primary">CLONE</button>
                    </div>
                </div>
            </details>

            <details class="group" id="details-theme-edit">
                <summary class="cursor-pointer text-[10px] font-black text-[#00f3ff] uppercase tracking-[0.2em] hover:text-white transition inline-block px-2">
                    &lt;/&gt; EDIT_SOURCE_CODE
                </summary>
                <div class="animate-drop-fade mt-6 p-8 rounded-lg shadow-2xl absolute z-50 w-full left-0 right-0 border border-[#00f3ff] bg-[#0f051e]/95 backdrop-blur-xl">
                    <div class="flex justify-between items-center mb-4">
                        <span class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em]">RAW HTML OVERRIDE</span>
                        <span class="text-[10px] text-[#ff00a0] font-bold uppercase tracking-widest animate-pulse">WARNING: CORE SYSTEM OVERRIDE</span>
                    </div>
                    <textarea id="theme-code-editor" class="w-full h-[500px] neon-input font-mono text-xs p-4 rounded outline-none" spellcheck="false"></textarea>
                    <div class="mt-6 flex gap-4 items-center">
                        <button onclick="saveThemeCode(event)" class="px-8 py-3 rounded text-xs neon-btn-primary">COMPILE_AND_SAVE</button>
                        <button onclick="loadThemeCode()" class="text-[10px] text-indigo-400 font-bold uppercase tracking-widest hover:text-white transition">ABORT</button>
                    </div>
                </div>
            </details>

            <button onclick="deleteCurrentTheme()" class="cursor-pointer text-[10px] font-black text-red-500 uppercase tracking-[0.2em] hover:text-[#ff00a0] transition inline-block px-2">
                [ - ] PURGE_THEME
            </button>
        </div>

        <div id="dynamic-content"></div>

        <footer class="mt-32 pt-10 border-t border-[#1c0936] flex justify-between items-center text-indigo-500 text-[10px] tracking-[0.3em] font-bold uppercase">
            <span>// LOCAL_NET_ESTABLISHED</span>
            <span class="flex items-center gap-3">
                <span class="w-2 h-2 rounded-full bg-[#00f3ff] animate-pulse shadow-[0_0_8px_#00f3ff]"></span>STATUS: OPTIMAL
            </span>
        </footer>
    </div>

    <script>
        let globalCategories = [];
        const detailsService = document.getElementById('details-service');
        const detailsCategory = document.getElementById('details-category');
        const detailsThemeClone = document.getElementById('details-theme-clone');
        const detailsThemeEdit = document.getElementById('details-theme-edit');

        const allDetails = [detailsService, detailsCategory, detailsThemeClone, detailsThemeEdit];
        allDetails.forEach(detail => {
            detail.addEventListener('toggle', () => {
                if (detail.open) {
                    allDetails.forEach(other => { if (other !== detail) other.removeAttribute('open'); });
                    
                    const animatedChild = detail.querySelector('.animate-drop-fade');
                    if(animatedChild) {
                        animatedChild.classList.remove('animate-drop-fade');
                        void animatedChild.offsetWidth; // force reflow
                        animatedChild.classList.add('animate-drop-fade');
                    }
                    if (detail === detailsThemeEdit) loadThemeCode(); 
                }
            });
        });
        
        function toggleEditMode() {
            document.body.classList.toggle('edit-mode');
            const btn = document.getElementById('edit-mode-btn');
            
            if(document.body.classList.contains('edit-mode')) {
                btn.classList.add('text-[#00f3ff]', 'border-[#00f3ff]', 'bg-[#00f3ff]/10');
                btn.classList.remove('text-indigo-400', 'border-[#3b1b63]', 'bg-[#1a1a1a]/50');
            } else {
                btn.classList.remove('text-[#00f3ff]', 'border-[#00f3ff]', 'bg-[#00f3ff]/10');
                btn.classList.add('text-indigo-400', 'border-[#3b1b63]', 'bg-[#1a1a1a]/50');
                allDetails.forEach(d => d.removeAttribute('open'));
            }
        }

        function toggleDropdown(id, event) {
            event.stopPropagation();
            const dropdown = document.getElementById(id);
            
            document.querySelectorAll('[id$="-dropdown"]').forEach(d => {
                if (d.id !== id) d.classList.add('hidden');
            });

            if (dropdown.classList.contains('hidden')) {
                dropdown.classList.remove('hidden');
                dropdown.classList.remove('animate-drop-fade');
                void dropdown.offsetWidth;
                dropdown.classList.add('animate-drop-fade');
            } else {
                dropdown.classList.add('hidden');
            }
        }

        document.addEventListener('click', () => {
            document.querySelectorAll('[id$="-dropdown"]').forEach(d => d.classList.add('hidden'));
        });

        async function init() { 
            await fetchThemes(); await fetchCategories(); await fetchServices(); 
        }

        async function fetchThemes() {
            try {
                const [themesRes, configRes] = await Promise.all([ fetch('/api/themes'), fetch('/api/config') ]);
                const themes = await themesRes.json();
                const config = await configRes.json();
                
                document.getElementById('theme-selected-text').textContent = config.theme;
                document.getElementById('theme-selector').value = config.theme;

                const optionsContainer = document.getElementById('theme-options');
                optionsContainer.innerHTML = '';
                themes.forEach(t => {
                    const a = document.createElement('a'); a.href = '#';
                    a.className = 'block px-4 py-3 text-[10px] text-indigo-300 hover:bg-[#ff00a0]/20 hover:text-white uppercase font-black tracking-widest transition-all border-b border-white/5';
                    a.textContent = t;
                    a.onclick = (e) => { e.preventDefault(); changeTheme(t); };
                    optionsContainer.appendChild(a);
                });
            } catch (e) { }
        }

        function changeTheme(newTheme) {
            fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme: newTheme }) })
            .then(() => location.reload()); 
        }
        
        function cloneTheme() {
            const nameInput = document.getElementById('new-theme-name');
            const val = nameInput.value.trim();
            if (!val) return;
            fetch('/api/themes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: val }) })
            .then(() => location.reload()); 
        }

        function deleteCurrentTheme() {
            const currentTheme = document.getElementById('theme-selector').value;
            if (currentTheme === 'default') { alert("ERROR: CORE_DEFAULT_THEME_PROTECTED"); return; }
            if (confirm(`WARNING: IRREVERSIBLE ACTION.\\nPurge the '${currentTheme}' theme from the system?`)) {
                fetch(`/api/themes/${currentTheme}`, { method: 'DELETE' }).then(res => {
                    if (res.ok) location.reload();
                });
            }
        }

        async function loadThemeCode() {
            const currentTheme = document.getElementById('theme-selector').value;
            const res = await fetch(`/api/themes/${currentTheme}`);
            const data = await res.json();
            document.getElementById('theme-code-editor').value = data.content;
        }

        async function saveThemeCode(event) {
            const currentTheme = document.getElementById('theme-selector').value;
            const content = document.getElementById('theme-code-editor').value;
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = "SAVING...";
            try {
                const response = await fetch(`/api/themes/${currentTheme}`, {
                    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content })
                });
                if (!response.ok) throw new Error();
                location.reload();
            } catch (error) {
                alert(`Failed to save theme!`);
                btn.innerText = originalText;
            }
        }

        async function fetchCategories() {
            try {
                const res = await fetch('/api/categories');
                globalCategories = await res.json();
                const optionsContainer = document.getElementById('category-options');
                optionsContainer.innerHTML = '';
                if(globalCategories.length > 0) {
                    document.getElementById('category-selected-text').textContent = globalCategories[0];
                    document.getElementById('category').value = globalCategories[0];
                }
                globalCategories.forEach(cat => {
                    const a = document.createElement('a'); a.href = '#';
                    a.className = 'block px-4 py-3 text-xs text-white hover:bg-[#00f3ff]/10 transition-all border-b border-white/5';
                    a.textContent = cat;
                    a.onclick = (e) => { e.preventDefault(); document.getElementById('category-selected-text').textContent = cat; document.getElementById('category').value = cat; };
                    optionsContainer.appendChild(a);
                });
            } catch (e) { }
        }

        async function fetchServices() {
            try {
                const res = await fetch('/api/services');
                const services = await res.json();
                renderDashboard(services);
            } catch (e) { }
        }

        function renderDashboard(services) {
            const container = document.getElementById('dynamic-content');
            container.innerHTML = '';
            const grouped = {};
            globalCategories.forEach(cat => grouped[cat] = []); 
            services.forEach(srv => { if (grouped[srv.category]) grouped[srv.category].push(srv); });

            for (const [category, items] of Object.entries(grouped)) {
                if (items.length === 0) continue;
                const section = document.createElement('section');
                section.className = 'mb-16';
                section.innerHTML = `
                    <h2 class="section-title mb-8 flex justify-between items-center group/cat">
                        <span>[ ${category} ]</span>
                        <button onclick="deleteCategory('${category}')" class="edit-mode-only text-indigo-700 hover:text-red-500 opacity-0 group-hover/cat:opacity-100 transition text-[9px] font-black uppercase tracking-widest">Remove Group</button>
                    </h2>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        ${items.map(srv => `
                            <a href="${srv.url}" target="_blank" class="service-card p-6 rounded-lg block relative group/card">
                                <div class="text-[#00f3ff] font-black tracking-wider text-sm mb-1 uppercase">${srv.name}</div>
                                <div class="text-[10px] text-indigo-300 font-medium tracking-wide opacity-70">${srv.desc || 'NO_DESCRIPTION'}</div>
                                <div class="absolute bottom-0 left-0 h-0.5 w-0 bg-[#00f3ff] group-hover/card:w-full transition-all duration-500 shadow-[0_0_10px_#00f3ff]"></div>
                                <button onclick="deleteService(event, '${srv.id}')" class="edit-mode-only absolute top-4 right-4 text-indigo-500 hover:text-[#ff00a0] opacity-0 group-hover/card:opacity-100 transition-opacity">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                                </button>
                            </a>
                        `).join('')}
                    </div>
                `;
                container.appendChild(section);
            }
        }

        function addCategory() {
            const val = document.getElementById('new-category-name').value.trim();
            if (!val) return;
            fetch('/api/categories', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: val }) }).then(() => location.reload());
        }
        function deleteCategory(catName) {
            if(confirm(`TERMINATE ${catName}?`)) fetch(`/api/categories/${encodeURIComponent(catName)}`, { method: 'DELETE' }).then(() => location.reload());
        }
        function addService() {
            const newService = {
                name: document.getElementById('name').value, desc: document.getElementById('desc').value,
                url: document.getElementById('url').value, category: document.getElementById('category').value
            };
            fetch('/api/services', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newService) }).then(() => location.reload());
        }
        function deleteService(event, id) {
            event.preventDefault(); 
            if(confirm('PURGE SERVICE?')) fetch(`/api/services/${id}`, { method: 'DELETE' }).then(() => location.reload());
        }
        init();
    </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# OCEAN THEME HTML 
# ---------------------------------------------------------------------------
OCEAN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ocean Server Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --sea-dark: #00080f;
            --sea-mid: #001a33;
            --sea-light: #002b4d;
            --cyan-glow: #38bdf8;
        }

        body { 
            background-color: var(--sea-dark); 
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(0, 43, 77, 0.4) 0%, transparent 50%),
                radial-gradient(circle at 85% 30%, rgba(0, 34, 61, 0.4) 0%, transparent 50%);
            background-size: 200% 200%;
            animation: oceanCurrents 15s ease infinite alternate;
            color: #b3d9ff; 
            font-family: 'Inter', system-ui, sans-serif; 
            min-height: 100vh;
            overflow-x: hidden;
        }

        @keyframes oceanCurrents {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
        }

        .ambient-glow {
            position: absolute; top: -100px; left: 50%; transform: translateX(-50%);
            width: 80vw; height: 300px; pointer-events: none; z-index: -1;
            background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.08) 0%, transparent 60%);
        }

        .service-card { 
            background: linear-gradient(145deg, rgba(10, 31, 46, 0.6) 0%, rgba(5, 15, 23, 0.4) 100%);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(56, 189, 248, 0.1); 
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            border-radius: 1rem;
            transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
            position: relative; overflow: hidden;
        }

        .service-card::before {
            content: ''; position: absolute; inset: 0; border-radius: inherit; padding: 1px;
            background: linear-gradient(to bottom right, rgba(255,255,255,0.1), transparent 50%);
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none;
        }

        .service-card:hover { 
            background: linear-gradient(145deg, rgba(14, 46, 70, 0.8) 0%, rgba(10, 31, 46, 0.6) 100%);
            border-color: rgba(56, 189, 248, 0.4); 
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 12px 40px rgba(56, 189, 248, 0.15);
        }

        @keyframes breathe {
            0%, 100% { opacity: 0.6; box-shadow: 0 0 8px var(--cyan-glow); }
            50% { opacity: 1; box-shadow: 0 0 16px var(--cyan-glow), 0 0 2px #fff; }
        }
        .status-line { animation: breathe 3s ease-in-out infinite; }

        .section-title { 
            color: #7dd3fc; letter-spacing: 0.2em; text-transform: uppercase; 
            font-size: 0.7rem; font-weight: 800; border-bottom: 1px solid rgba(56, 189, 248, 0.15);
            padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;
        }

        details > summary { list-style: none; user-select: none; }
        details > summary::-webkit-details-marker { display: none; }
        
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--sea-dark); }
        ::-webkit-scrollbar-thumb { background: rgba(56, 189, 248, 0.3); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(56, 189, 248, 0.6); }

        @keyframes dropFade {
            0% { opacity: 0; transform: translateY(-10px) scale(0.98); filter: blur(4px); }
            100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }
        .animate-drop-fade {
            animation: dropFade 0.3s cubic-bezier(0.2, 0.8, 0.2, 1) both;
            transform-origin: top center;
        }

        input, select, textarea {
            background: rgba(0, 11, 20, 0.6) !important;
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
            color: #e0f2fe !important; backdrop-filter: blur(8px);
        }
        input:focus, textarea:focus { border-color: var(--cyan-glow) !important; box-shadow: 0 0 10px rgba(56,189,248,0.1); }

        body { border-top: 3px solid transparent; transition: border-color 0.4s ease; }
        body.edit-mode { border-top-color: #f43f5e; }
        
        body:not(.edit-mode) .edit-mode-only { display: none !important; }
        body.edit-mode .edit-mode-only { animation: editFadeIn 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
        
        @keyframes editFadeIn {
            0% { opacity: 0; transform: translateY(-15px) scale(0.98); filter: blur(4px); }
            100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }
    </style>
</head>
<body class="p-6 md:p-16 relative">
    <div class="ambient-glow"></div>
    <div class="max-w-5xl mx-auto relative z-10">
        <header class="mb-16 flex items-center justify-between">
            <div class="flex items-center gap-6 group">
                <div class="relative">
                    <svg class="h-12 w-12 text-sky-400 drop-shadow-[0_0_8px_rgba(56,189,248,0.5)] transition-transform duration-500 group-hover:scale-110" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
                    </svg>
                </div>
                <div>
                    <h1 class="text-3xl font-light tracking-tight text-sky-50">System <span class="font-bold text-sky-400">Dashboard</span></h1>
                    <div class="status-line h-1 w-16 bg-sky-400 mt-2 rounded-full"></div>
                </div>
            </div>
            
            <div class="flex items-center gap-4">
                <button id="edit-mode-btn" onclick="toggleEditMode()" class="flex items-center gap-2 bg-[#001524]/80 backdrop-blur text-sky-400 border border-sky-900/50 py-2.5 px-5 rounded-lg text-xs focus:outline-none transition-all uppercase tracking-widest font-bold hover:bg-sky-900/40 hover:text-white hover:border-sky-400/50">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                    <span id="edit-btn-text">Edit UI</span>
                </button>

                <div class="relative inline-block text-left">
                    <button type="button" onclick="toggleDropdown('theme-dropdown', event)" class="flex items-center gap-2 bg-[#001524]/80 backdrop-blur text-sky-400 border border-sky-900/50 py-2.5 pl-5 pr-4 rounded-lg text-xs focus:outline-none transition-all uppercase tracking-widest font-bold hover:bg-sky-900/40 hover:border-sky-400/50">
                        <span id="theme-selected-text">OCEAN THEME</span>
                        <svg class="w-4 h-4 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                    <div id="theme-dropdown" class="hidden animate-drop-fade origin-top-right absolute right-0 mt-3 w-48 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.5)] bg-[#001524]/95 backdrop-blur-xl border border-sky-900/50 z-50 overflow-hidden">
                        <div class="py-2" id="theme-options"></div>
                    </div>
                    <input type="hidden" id="theme-selector" value="ocean">
                </div>
            </div>
        </header>

        <div class="flex flex-wrap gap-4 mb-12 relative edit-mode-only bg-rose-950/20 p-4 rounded-xl border border-rose-900/30 backdrop-blur-sm">
            <details class="group" id="details-service">
                <summary class="cursor-pointer text-xs font-bold text-sky-400 uppercase tracking-widest hover:text-white transition inline-block px-3 py-2 rounded-lg hover:bg-sky-900/30">
                    + Add Service
                </summary>
                <div class="animate-drop-fade mt-4 p-8 bg-[#001524]/95 backdrop-blur-xl border border-sky-800/50 rounded-2xl shadow-2xl absolute z-40 w-full max-w-4xl left-0">
                    <h3 class="text-sky-400 text-xs font-bold uppercase tracking-widest mb-4">Deploy New Service</h3>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                        <input type="text" id="name" placeholder="Name" class="p-3.5 rounded-lg text-sm transition w-full outline-none">
                        <input type="text" id="desc" placeholder="Description" class="p-3.5 rounded-lg text-sm transition w-full outline-none">
                        <input type="text" id="url" placeholder="URL" class="p-3.5 rounded-lg text-sm transition w-full outline-none">
                        <div class="relative w-full">
                            <button type="button" onclick="toggleDropdown('category-dropdown', event)" class="flex justify-between items-center bg-[rgba(0,11,20,0.6)] text-white border border-sky-900/40 p-3.5 rounded-lg text-sm focus:border-sky-400 outline-none transition w-full hover:bg-sky-900/30">
                                <span id="category-selected-text" class="truncate">Select Category...</span>
                                <svg class="w-4 h-4 text-sky-500 ml-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </button>
                            <div id="category-dropdown" class="hidden animate-drop-fade absolute z-50 w-full mt-2 rounded-xl shadow-2xl bg-[#001524] border border-sky-800/50 max-h-48 overflow-y-auto">
                                <div class="py-2" id="category-options"></div>
                            </div>
                            <input type="hidden" id="category" value="">
                        </div>
                    </div>
                    <div class="mt-8 flex justify-end">
                        <button onclick="addService()" class="bg-sky-500 text-white px-8 py-3 rounded-lg text-sm font-bold hover:bg-sky-400 transition shadow-[0_0_20px_rgba(14,165,233,0.3)] hover:shadow-[0_0_30px_rgba(14,165,233,0.5)]">Save Service</button>
                    </div>
                </div>
            </details>

            <details class="group" id="details-category">
                <summary class="cursor-pointer text-xs font-bold text-sky-400 uppercase tracking-widest hover:text-white transition inline-block px-3 py-2 rounded-lg hover:bg-sky-900/30">
                    + Add Category
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#001524]/95 backdrop-blur-xl border border-sky-800/50 rounded-2xl shadow-2xl absolute z-40 w-full max-w-md left-0 sm:left-auto">
                    <div class="flex gap-4">
                        <input type="text" id="new-category-name" placeholder="Category Name" class="p-3.5 rounded-lg text-sm transition w-full flex-1 outline-none">
                        <button onclick="addCategory()" class="bg-sky-500 text-white px-6 py-3 rounded-lg text-sm font-bold hover:bg-sky-400 transition">Add</button>
                    </div>
                </div>
            </details>

            <details class="group" id="details-theme-clone">
                <summary class="cursor-pointer text-xs font-bold text-sky-400 uppercase tracking-widest hover:text-white transition inline-block px-3 py-2 rounded-lg hover:bg-sky-900/30">
                    + Clone Theme
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#001524]/95 backdrop-blur-xl border border-sky-800/50 rounded-2xl shadow-2xl absolute z-40 w-full max-w-md left-0 sm:left-auto">
                    <div class="flex gap-4">
                        <input type="text" id="new-theme-name" placeholder="New Theme Name (e.g. Ocean)" class="p-3.5 rounded-lg text-sm transition w-full flex-1 outline-none">
                        <button onclick="cloneTheme()" class="bg-sky-500 text-white px-6 py-3 rounded-lg text-sm font-bold hover:bg-sky-400 transition">Clone</button>
                    </div>
                </div>
            </details>

            <details class="group" id="details-theme-edit">
                <summary class="cursor-pointer text-xs font-bold text-cyan-300 uppercase tracking-widest hover:text-white transition inline-block px-3 py-2 rounded-lg hover:bg-sky-900/30">
                    &lt;/&gt; Edit Theme Code
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#001524]/95 backdrop-blur-xl border border-sky-800/50 rounded-2xl shadow-2xl absolute z-50 w-full left-0 right-0">
                    <textarea id="theme-code-editor" class="w-full h-[500px] bg-[#00080f] text-cyan-300 font-mono text-sm p-5 border border-sky-900/50 rounded-xl outline-none focus:border-sky-400 transition leading-relaxed shadow-inner" spellcheck="false"></textarea>
                    <div class="mt-6 flex gap-4 justify-end">
                        <button onclick="loadThemeCode()" class="text-sky-500 hover:text-sky-300 text-sm font-semibold transition px-4 py-2">Discard Changes</button>
                        <button onclick="saveThemeCode(event)" class="bg-cyan-600 text-white px-8 py-3 rounded-lg text-sm font-bold hover:bg-cyan-500 transition shadow-[0_0_20px_rgba(8,145,178,0.4)]">Save & Compile</button>
                    </div>
                </div>
            </details>

            <button onclick="deleteCurrentTheme()" class="cursor-pointer text-xs font-bold text-rose-500 uppercase tracking-widest hover:text-white transition inline-block px-3 py-2 rounded-lg hover:bg-rose-900/30">
                - Delete Theme
            </button>
        </div>

        <div id="dynamic-content"></div>

        <footer class="mt-32 pb-8 border-t border-sky-900/30 pt-8 flex justify-between items-center text-sky-700 text-[10px] tracking-[0.2em] uppercase font-bold">
            <span class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-sky-500 animate-pulse"></div>
                Local Subnet
            </span>
            <span>All Systems Hydrated</span>
        </footer>
    </div>

    <script>
        let globalCategories = [];
        const detailsService = document.getElementById('details-service');
        const detailsCategory = document.getElementById('details-category');
        const detailsThemeClone = document.getElementById('details-theme-clone');
        const detailsThemeEdit = document.getElementById('details-theme-edit');

        const allDetails = [detailsService, detailsCategory, detailsThemeClone, detailsThemeEdit];
        allDetails.forEach(detail => {
            detail.addEventListener('toggle', () => {
                if (detail.open) {
                    allDetails.forEach(other => { if (other !== detail) other.removeAttribute('open'); });
                    
                    const animatedChild = detail.querySelector('.animate-drop-fade');
                    if(animatedChild) {
                        animatedChild.classList.remove('animate-drop-fade');
                        void animatedChild.offsetWidth; // force reflow
                        animatedChild.classList.add('animate-drop-fade');
                    }

                    if (detail.id === 'details-theme-edit') loadThemeCode(); 
                }
            });
        });

        function toggleEditMode() {
            document.body.classList.toggle('edit-mode');
            const btn = document.getElementById('edit-mode-btn');
            const btnText = document.getElementById('edit-btn-text');
            if(document.body.classList.contains('edit-mode')) {
                btn.classList.add('bg-rose-500', 'text-white', 'border-rose-400');
                btn.classList.remove('bg-[#001524]/80', 'text-sky-400', 'border-sky-900/50');
                btnText.textContent = 'Lock UI';
            } else {
                btn.classList.remove('bg-rose-500', 'text-white', 'border-rose-400');
                btn.classList.add('bg-[#001524]/80', 'text-sky-400', 'border-sky-900/50');
                btnText.textContent = 'Edit UI';
                allDetails.forEach(d => d.removeAttribute('open'));
            }
        }
        
        function toggleDropdown(id, event) {
            event.stopPropagation();
            const dropdown = document.getElementById(id);
            
            document.querySelectorAll('[id$="-dropdown"]').forEach(d => {
                if (d.id !== id) d.classList.add('hidden');
            });

            if (dropdown.classList.contains('hidden')) {
                dropdown.classList.remove('hidden');
                dropdown.classList.remove('animate-drop-fade');
                void dropdown.offsetWidth;
                dropdown.classList.add('animate-drop-fade');
            } else {
                dropdown.classList.add('hidden');
            }
        }

        document.addEventListener('click', () => {
            document.querySelectorAll('[id$="-dropdown"]').forEach(d => d.classList.add('hidden'));
        });

        async function init() { 
            await fetchThemes(); await fetchCategories(); await fetchServices(); 
        }

        async function fetchThemes() {
            try {
                const [themesRes, configRes] = await Promise.all([ fetch('/api/themes'), fetch('/api/config') ]);
                const themes = await themesRes.json();
                const config = await configRes.json();
                
                document.getElementById('theme-selected-text').textContent = config.theme + ' THEME';
                document.getElementById('theme-selector').value = config.theme;

                const optionsContainer = document.getElementById('theme-options');
                optionsContainer.innerHTML = '';
                themes.forEach(t => {
                    const a = document.createElement('a'); a.href = '#';
                    a.className = 'block px-5 py-3 text-xs text-sky-200 hover:bg-sky-900/40 hover:text-white uppercase font-bold tracking-widest transition';
                    a.textContent = t + ' Theme';
                    a.onclick = (e) => { e.preventDefault(); changeTheme(t); };
                    optionsContainer.appendChild(a);
                });
            } catch (e) {}
        }

        function changeTheme(newTheme) {
            fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme: newTheme }) })
            .then(() => location.reload()); 
        }

        function cloneTheme() {
            const nameInput = document.getElementById('new-theme-name');
            const val = nameInput.value.trim();
            if (!val) return;
            fetch('/api/themes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: val }) })
            .then(() => location.reload()); 
        }

        function deleteCurrentTheme() {
            const currentTheme = document.getElementById('theme-selector').value;
            if (currentTheme === 'default') { alert("The default theme cannot be deleted."); return; }
            if (confirm(`Are you sure you want to delete the '${currentTheme}' theme?`)) {
                fetch(`/api/themes/${currentTheme}`, { method: 'DELETE' }).then(res => {
                    if (res.ok) { location.reload(); }
                });
            }
        }

        async function loadThemeCode() {
            const currentTheme = document.getElementById('theme-selector').value;
            const res = await fetch(`/api/themes/${currentTheme}`);
            const data = await res.json();
            document.getElementById('theme-code-editor').value = data.content;
        }

        async function saveThemeCode(event) {
            const currentTheme = document.getElementById('theme-selector').value;
            const content = document.getElementById('theme-code-editor').value;
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = "Saving...";
            
            try {
                const response = await fetch(`/api/themes/${currentTheme}`, {
                    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content })
                });
                if (!response.ok) throw new Error();
                location.reload(); 
            } catch (error) {
                alert(`Failed to save theme!`);
                btn.innerText = originalText;
            }
        }

        async function fetchCategories() {
            try {
                const res = await fetch('/api/categories');
                globalCategories = await res.json();
                const optionsContainer = document.getElementById('category-options');
                optionsContainer.innerHTML = '';
                
                if(globalCategories.length > 0) {
                    document.getElementById('category-selected-text').textContent = globalCategories[0];
                    document.getElementById('category').value = globalCategories[0];
                }
                
                globalCategories.forEach(cat => {
                    const a = document.createElement('a'); a.href = '#';
                    a.className = 'block px-5 py-3 text-sm text-sky-200 hover:bg-sky-900/40 hover:text-white transition';
                    a.textContent = cat;
                    a.onclick = (e) => { e.preventDefault(); document.getElementById('category-selected-text').textContent = cat; document.getElementById('category').value = cat; };
                    optionsContainer.appendChild(a);
                });
            } catch (e) {}
        }

        async function fetchServices() {
            try {
                const res = await fetch('/api/services');
                const services = await res.json();
                renderDashboard(services);
            } catch (e) {}
        }

        function renderDashboard(services) {
            const container = document.getElementById('dynamic-content');
            container.innerHTML = '';
            const grouped = {};
            globalCategories.forEach(cat => grouped[cat] = []); 
            services.forEach(srv => {
                if (grouped[srv.category] !== undefined) { grouped[srv.category].push(srv); } 
                else { if (!grouped['Other Services']) grouped['Other Services'] = []; grouped['Other Services'].push(srv); }
            });

            for (const [category, items] of Object.entries(grouped)) {
                if (items.length === 0) continue;
                const section = document.createElement('section');
                section.className = 'mb-12';
                section.innerHTML = `
                    <h2 class="section-title group/cat">
                        <span>${category}</span>
                        <button onclick="deleteCategory('${category}')" class="edit-mode-only text-sky-700 hover:text-rose-400 opacity-0 group-hover/cat:opacity-100 transition-all text-[10px] bg-rose-950/30 px-3 py-1.5 rounded-md border border-rose-900/50 tracking-widest uppercase">Delete</button>
                    </h2>`;
                const grid = document.createElement('div');
                grid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6';

                items.forEach(srv => {
                    let link = srv.url; if (link && !link.startsWith('http')) link = 'http://' + link;
                    const card = document.createElement('a');
                    card.href = link;
                    card.target = '_blank';
                    card.className = 'service-card p-6 block group/card';
                    card.innerHTML = `
                        <div class="relative z-10">
                            <div class="text-sky-50 font-semibold tracking-wide text-lg mb-1">${srv.name}</div>
                            <div class="text-xs text-sky-300/60 leading-relaxed font-light">${srv.desc || ''}</div>
                        </div>
                        <button onclick="deleteService(event, '${srv.id}')" class="edit-mode-only absolute top-4 right-4 z-20 text-sky-700 bg-rose-950/50 p-2 rounded-lg hover:text-rose-300 hover:bg-rose-900 opacity-0 group-hover/card:opacity-100 transition-all border border-rose-900/50">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        </button>`;
                    grid.appendChild(card);
                });
                section.appendChild(grid);
                container.appendChild(section);
            }
        }

        function addCategory() {
            const val = document.getElementById('new-category-name').value.trim();
            if (!val) return;
            fetch('/api/categories', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: val }) }).then(() => location.reload());
        }

        function deleteCategory(catName) {
            if(confirm(`Remove the '${catName}' category?`)) fetch(`/api/categories/${encodeURIComponent(catName)}`, { method: 'DELETE' }).then(() => location.reload());
        }

        function addService() {
            const newService = {
                name: document.getElementById('name').value, desc: document.getElementById('desc').value,
                url: document.getElementById('url').value, category: document.getElementById('category').value
            };
            if (!newService.name || !newService.url) return;
            fetch('/api/services', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newService) }).then(() => location.reload());
        }

        function deleteService(event, id) {
            event.preventDefault(); 
            if(confirm('Remove this service?')) fetch(`/api/services/${id}`, { method: 'DELETE' }).then(() => location.reload()); 
        }

        init();
    </script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# BACKEND LOGIC
# ---------------------------------------------------------------------------
def setup_environment():
    for d in [DATA_DIR, IMAGES_DIR, TEMPLATES_DIR]:
        os.makedirs(d, exist_ok=True)
    
    if not os.path.exists(SERVICES_FILE):
        with open(SERVICES_FILE, 'w') as f: json.dump([], f)
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'w') as f: json.dump(DEFAULT_CATEGORIES, f)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f: json.dump(DEFAULT_CONFIG, f)

    default_html_path = os.path.join(TEMPLATES_DIR, 'default.html')
    if not os.path.exists(default_html_path):
        with open(default_html_path, 'w') as f:
            f.write(DEFAULT_HTML)

    neon_html_path = os.path.join(TEMPLATES_DIR, 'neon.html')
    if not os.path.exists(neon_html_path):
        with open(neon_html_path, 'w') as f:
            f.write(NEON_HTML)
            
    ocean_html_path = os.path.join(TEMPLATES_DIR, 'ocean.html')
    if not os.path.exists(ocean_html_path):
        with open(ocean_html_path, 'w') as f:
            f.write(OCEAN_HTML)

setup_environment()

def load_json(path):
    with open(path, 'r') as f: return json.load(f)
def save_json(data, path):
    with open(path, 'w') as f: json.dump(data, f, indent=4)

@app.route('/')
def index():
    config = load_json(CONFIG_FILE)
    active_theme = config.get('theme', 'default')
    
    if not os.path.exists(os.path.join(TEMPLATES_DIR, f"{active_theme}.html")):
        active_theme = 'default'
        
    return render_template(f"{active_theme}.html")

@app.route('/api/themes', methods=['GET', 'POST'])
def handle_themes():
    if request.method == 'POST':
        raw_name = request.json.get('name', '').strip()
        safe_name = re.sub(r'[^a-zA-Z0-9-]', '', raw_name).lower()
        if not safe_name: return jsonify({"error": "Invalid theme name"}), 400
            
        new_file_path = os.path.join(TEMPLATES_DIR, f"{safe_name}.html")
        if not os.path.exists(new_file_path):
            with open(os.path.join(TEMPLATES_DIR, 'default.html'), 'r') as f:
                default_content = f.read()
            with open(new_file_path, 'w') as f:
                f.write(default_content)
                
            config = load_json(CONFIG_FILE)
            config['theme'] = safe_name
            save_json(config, CONFIG_FILE)
            
        return jsonify({"status": "success", "theme": safe_name}), 201
        
    themes = [f.replace('.html', '') for f in os.listdir(TEMPLATES_DIR) if f.endswith('.html')]
    return jsonify(themes)

@app.route('/api/themes/<theme_name>', methods=['GET', 'PUT', 'DELETE'])
def edit_theme_content(theme_name):
    safe_name = re.sub(r'[^a-zA-Z0-9-]', '', theme_name).lower()
    file_path = os.path.join(TEMPLATES_DIR, f"{safe_name}.html")
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Theme not found"}), 404

    if request.method == 'DELETE':
        if safe_name == 'default':
            return jsonify({"error": "Cannot delete the default theme."}), 403
            
        os.remove(file_path)
        
        config = load_json(CONFIG_FILE)
        if config.get('theme') == safe_name:
            config['theme'] = 'default'
            save_json(config, CONFIG_FILE)
            
        return jsonify({"status": "success"}), 200

    if request.method == 'PUT':
        content = request.json.get('content', '')
        with open(file_path, 'w') as f:
            f.write(content)
        return jsonify({"status": "success"}), 200

    with open(file_path, 'r') as f:
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