import json
import os
import uuid
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, 
            template_folder='/templates', 
            static_folder='/images', 
            static_url_path='/images')

DATA_DIR = '/data'
IMAGES_DIR = '/images'
TEMPLATES_DIR = '/templates'

SERVICES_FILE = os.path.join(DATA_DIR, 'services.json')
CATEGORIES_FILE = os.path.join(DATA_DIR, 'categories.json')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

DEFAULT_CATEGORIES = ["Media & Content", "Management & Network", "Ai & Generation"]
DEFAULT_CONFIG = {"theme": "default"}
NEON_CONFIG = {"theme": "neon"}
# The default theme HTML 
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
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0a0a0a; }
        ::-webkit-scrollbar-thumb { background: #262626; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #404040; }

        /* Smooth Fade & Slide Animation */
        @keyframes dropFade {
            0% { opacity: 0; transform: translateY(-8px) scale(0.98); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-drop-fade {
            animation: dropFade 0.2s ease-out forwards;
            transform-origin: top;
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
        </header>

        <div class="flex flex-wrap gap-8 mb-16 relative">
            <details class="group" id="details-service">
                <summary class="cursor-pointer text-xs font-bold text-neutral-500 uppercase tracking-widest hover:text-white transition inline-block">
                    + Add New Service
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#111] border border-[#262626] rounded-lg shadow-2xl absolute z-40 w-full max-w-4xl left-0">
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <input type="text" id="name" placeholder="Name (e.g. Nextcloud)" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full">
                        <input type="text" id="desc" placeholder="Description (e.g. Files & Storage)" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full">
                        <input type="text" id="url" placeholder="URL (e.g. https://nextcloud.lan)" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full">
                        
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
                <summary class="cursor-pointer text-xs font-bold text-neutral-500 uppercase tracking-widest hover:text-white transition inline-block">
                    + Add New Category
                </summary>
                <div class="animate-drop-fade mt-4 p-6 bg-[#111] border border-[#262626] rounded-lg shadow-2xl absolute z-40 w-full max-w-md left-0 sm:left-auto">
                    <div class="flex gap-4">
                        <input type="text" id="new-category-name" placeholder="Category Name" class="bg-[#1a1a1a] text-white border border-[#333] p-3 rounded text-sm focus:border-white outline-none transition w-full flex-1">
                        <button onclick="addCategory()" class="bg-white text-black px-4 py-2.5 rounded text-sm font-semibold hover:bg-gray-200 transition">Add</button>
                    </div>
                </div>
            </details>
        </div>

        <div id="dynamic-content"></div>

        <footer class="mt-24 pt-8 border-t border-neutral-900 flex justify-between items-center text-neutral-600 text-xs tracking-widest uppercase">
            <span>Local Network</span>
            <span>All Systems Operational</span>
        </footer>
    </div>

    <script>
        let globalCategories = [];
        
        // Fix the overlapping menus
        const detailsService = document.getElementById('details-service');
        const detailsCategory = document.getElementById('details-category');

        detailsService.addEventListener('toggle', () => {
            if (detailsService.open) detailsCategory.removeAttribute('open');
        });

        detailsCategory.addEventListener('toggle', () => {
            if (detailsCategory.open) detailsService.removeAttribute('open');
        });
        
        // Custom Dropdown Logic
        function toggleDropdown(id, event) {
            event.stopPropagation();
            const dropdown = document.getElementById(id);
            if (id !== 'theme-dropdown') document.getElementById('theme-dropdown').classList.add('hidden');
            if (id !== 'category-dropdown') document.getElementById('category-dropdown').classList.add('hidden');
            dropdown.classList.toggle('hidden');
        }

        document.addEventListener('click', () => {
            document.getElementById('theme-dropdown').classList.add('hidden');
            document.getElementById('category-dropdown').classList.add('hidden');
        });

        async function init() { 
            await fetchThemes();
            await fetchCategories(); 
            await fetchServices(); 
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
                a.onclick = (e) => {
                    e.preventDefault();
                    document.getElementById('theme-selector').value = t;
                    changeTheme(t);
                };
                optionsContainer.appendChild(a);
            });
        }

        function changeTheme(newTheme) {
            fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme: newTheme }) })
            .then(() => location.reload()); 
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
                const a = document.createElement('a');
                a.href = '#';
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
                const cat = srv.category;
                if (grouped[cat] !== undefined) { grouped[cat].push(srv); } 
                else { if (!grouped['Other Services']) grouped['Other Services'] = []; grouped['Other Services'].push(srv); }
            });

            for (const [category, items] of Object.entries(grouped)) {
                if (items.length === 0) continue;
                const section = document.createElement('section');
                section.className = 'mb-16';
                const title = document.createElement('h2');
                title.className = 'section-title mb-6 flex justify-between items-center group/cat';
                title.innerHTML = `<span>${category}</span><button onclick="deleteCategory('${category}')" class="text-neutral-700 hover:text-red-500 opacity-0 group-hover/cat:opacity-100 transition text-xs font-normal lowercase tracking-normal">remove</button>`;
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
                        <button onclick="deleteService(event, '${srv.id}')" class="absolute top-4 right-4 text-neutral-600 hover:text-red-500 opacity-0 group-hover/card:opacity-100 transition-opacity">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        </button>`;
                    grid.appendChild(a);
                });
                section.appendChild(grid);
                container.appendChild(section);
            }
        }

        function addCategory() {
            const nameInput = document.getElementById('new-category-name');
            const newCat = nameInput.value.trim();
            if (!newCat) return;
            fetch('/api/categories', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newCat }) })
            .then(() => { nameInput.value = ''; document.getElementById('details-category').removeAttribute('open'); init(); });
        }

        function deleteCategory(catName) {
            if(confirm(`Remove the '${catName}' category?`)) {
                fetch(`/api/categories/${encodeURIComponent(catName)}`, { method: 'DELETE' }).then(() => init());
            }
        }

        function addService() {
            const newService = {
                name: document.getElementById('name').value, desc: document.getElementById('desc').value,
                url: document.getElementById('url').value, category: document.getElementById('category').value
            };
            if (!newService.name || !newService.url) { alert("Name and URL required."); return; }
            fetch('/api/services', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newService) })
            .then(() => { document.getElementById('name').value = ''; document.getElementById('desc').value = ''; document.getElementById('url').value = ''; document.getElementById('details-service').removeAttribute('open'); init(); });
        }

        function deleteService(event, id) {
            event.preventDefault(); 
            if(confirm('Remove this service?')) { fetch(`/api/services/${id}`, { method: 'DELETE' }).then(() => init()); }
        }
        init();
    </script>
</body>
</html>"""

# The Neon theme (second theme)
NEON_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Server Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --neon-cyan: #00f3ff;
            --neon-pink: #ff00a0;
            --bg-deep: #06040d;
            --glass: rgba(15, 5, 30, 0.85);
        }

        body { 
            background-color: var(--bg-deep); 
            background-image: 
                radial-gradient(circle at 50% 0%, #1c0936 0%, transparent 50%),
                linear-gradient(rgba(18, 16, 33, 0.3) 1px, transparent 1px),
                linear-gradient(90deg, rgba(18, 16, 33, 0.3) 1px, transparent 1px);
            background-size: 100% 100%, 30px 30px, 30px 30px;
            color: #e5e5e5; 
            font-family: 'Inter', system-ui, sans-serif; 
            min-height: 100vh;
        }

        /* Neon Service Cards */
        .service-card { 
            background: rgba(20, 10, 40, 0.5); 
            backdrop-filter: blur(8px);
            border: 1px solid #3b1b63; 
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        }
        .service-card:hover { 
            background: rgba(30, 15, 60, 0.7); 
            border-color: var(--neon-cyan); 
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.2), inset 0 0 10px rgba(0, 243, 255, 0.1);
            transform: translateY(-4px); 
        }

        .section-title { 
            color: var(--neon-pink); 
            letter-spacing: 0.15em; 
            text-transform: uppercase; 
            font-size: 0.75rem; 
            font-weight: 800;
            text-shadow: 0 0 8px rgba(255, 0, 160, 0.4);
        }
        
        /* Custom UI Components */
        .neon-input {
            background: rgba(10, 5, 20, 0.8) !important;
            border: 1px solid #3b1b63 !important;
            color: var(--neon-cyan) !important;
        }
        .neon-input:focus {
            border-color: var(--neon-cyan) !important;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);
            outline: none;
        }

        .neon-dropdown {
            background: var(--glass) !important;
            border: 1px solid var(--neon-cyan) !important;
            backdrop-filter: blur(12px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 243, 255, 0.1);
        }

        .neon-btn-primary {
            background: var(--neon-cyan);
            color: #000;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            box-shadow: 0 0 15px rgba(0, 243, 255, 0.4);
            transition: all 0.2s;
        }
        .neon-btn-primary:hover {
            background: #fff;
            box-shadow: 0 0 25px var(--neon-cyan);
        }

        details > summary { list-style: none; }
        details > summary::-webkit-details-marker { display: none; }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-deep); }
        ::-webkit-scrollbar-thumb { background: #3b1b63; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--neon-pink); }

        /* Animation */
        @keyframes dropFade {
            0% { opacity: 0; transform: translateY(-12px) scale(0.95); filter: blur(4px); }
            100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }
        .animate-drop-fade {
            animation: dropFade 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
            transform-origin: top;
        }
    </style>
</head>
<body class="p-6 md:p-16">
    <div class="max-w-5xl mx-auto">
        <header class="mb-16 flex items-center justify-between">
            <div class="flex items-center gap-6">
                <svg class="h-12 w-12 text-[#ff00a0] drop-shadow-[0_0_8px_rgba(255,0,160,0.6)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                    <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                    <line x1="6" y1="6" x2="6.01" y2="6"></line>
                    <line x1="6" y1="18" x2="6.01" y2="18"></line>
                </svg>
                <div>
                    <h1 class="text-2xl font-light tracking-tighter text-white">SYSTEM <span class="font-black text-[#00f3ff]">CORE</span></h1>
                    <div class="h-0.5 w-12 bg-[#ff00a0] mt-1 shadow-[0_0_10px_#ff00a0]"></div>
                </div>
            </div>
            
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
        </header>

        <div class="flex flex-wrap gap-8 mb-20 relative">
            <details class="group" id="details-service">
                <summary class="cursor-pointer text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] hover:text-[#00f3ff] transition inline-block">
                    [ + ] INITIALIZE_SERVICE
                </summary>
                <div class="animate-drop-fade mt-6 p-8 rounded-lg shadow-2xl absolute z-40 w-full max-w-4xl left-0 border border-[#ff00a0] bg-[#0f051e]/95 backdrop-blur-xl">
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div class="space-y-1">
                            <label class="text-[9px] font-bold text-indigo-400 ml-1">NAME</label>
                            <input type="text" id="name" placeholder="Plex" class="neon-input p-3 rounded text-sm w-full">
                        </div>
                        <div class="space-y-1">
                            <label class="text-[9px] font-bold text-indigo-400 ml-1">INFO</label>
                            <input type="text" id="desc" placeholder="Media Server" class="neon-input p-3 rounded text-sm w-full">
                        </div>
                        <div class="space-y-1">
                            <label class="text-[9px] font-bold text-indigo-400 ml-1">ADDRESS</label>
                            <input type="text" id="url" placeholder="192.168.1.50" class="neon-input p-3 rounded text-sm w-full">
                        </div>
                        <div class="space-y-1">
                            <label class="text-[9px] font-bold text-indigo-400 ml-1">GROUP</label>
                            <div class="relative w-full">
                                <button type="button" onclick="toggleDropdown('category-dropdown', event)" class="flex justify-between items-center neon-input p-3 rounded text-sm w-full hover:bg-white/5 transition-all">
                                    <span id="category-selected-text" class="truncate">Select Group...</span>
                                    <svg class="w-4 h-4 text-indigo-400 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                </button>
                                <div id="category-dropdown" class="hidden animate-drop-fade absolute z-50 w-full mt-2 rounded-md neon-dropdown max-h-48 overflow-y-auto">
                                    <div class="py-1" id="category-options"></div>
                                </div>
                                <input type="hidden" id="category" value="">
                            </div>
                        </div>
                    </div>
                    <button onclick="addService()" class="mt-8 px-8 py-3 rounded text-xs neon-btn-primary">Deploy Service</button>
                </div>
            </details>

            <details class="group" id="details-category">
                <summary class="cursor-pointer text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] hover:text-[#ff00a0] transition inline-block">
                    [ + ] CREATE_GROUP
                </summary>
                <div class="animate-drop-fade mt-6 p-8 rounded-lg shadow-2xl absolute z-40 w-full max-w-md left-0 sm:left-auto border border-[#ff00a0] bg-[#0f051e]/95 backdrop-blur-xl">
                    <div class="flex gap-4 items-end">
                        <div class="flex-1 space-y-1">
                            <label class="text-[9px] font-bold text-indigo-400 ml-1">GROUP_NAME</label>
                            <input type="text" id="new-category-name" class="neon-input p-3 rounded text-sm w-full">
                        </div>
                        <button onclick="addCategory()" class="px-6 py-3 rounded text-xs neon-btn-primary">ADD</button>
                    </div>
                </div>
            </details>
        </div>

        <div id="dynamic-content"></div>

        <footer class="mt-32 pt-10 border-t border-[#1c0936] flex justify-between items-center text-indigo-500 text-[10px] tracking-[0.3em] font-bold uppercase">
            <span>// LOCAL_NET_ESTABLISHED</span>
            <span class="flex items-center gap-3">
                <span class="w-2 h-2 rounded-full bg-[#00f3ff] animate-pulse shadow-[0_0_8px_#00f3ff]"></span>
                STATUS: OPTIMAL
            </span>
        </footer>
    </div>

    <script>
        let globalCategories = [];
        const detailsService = document.getElementById('details-service');
        const detailsCategory = document.getElementById('details-category');

        detailsService.addEventListener('toggle', () => {
            if (detailsService.open) detailsCategory.removeAttribute('open');
        });

        detailsCategory.addEventListener('toggle', () => {
            if (detailsCategory.open) detailsService.removeAttribute('open');
        });
        
        function toggleDropdown(id, event) {
            event.stopPropagation();
            const dropdown = document.getElementById(id);
            // Close others
            if (id !== 'theme-dropdown') document.getElementById('theme-dropdown').classList.add('hidden');
            if (id !== 'category-dropdown') document.getElementById('category-dropdown').classList.add('hidden');
            dropdown.classList.toggle('hidden');
        }

        document.addEventListener('click', () => {
            document.getElementById('theme-dropdown').classList.add('hidden');
            document.getElementById('category-dropdown').classList.add('hidden');
        });

        async function init() { 
            await fetchThemes();
            await fetchCategories(); 
            await fetchServices(); 
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
                    const a = document.createElement('a');
                    a.href = '#';
                    a.className = 'block px-4 py-3 text-[10px] text-indigo-300 hover:bg-[#ff00a0]/20 hover:text-white uppercase font-black tracking-widest transition-all border-b border-white/5';
                    a.textContent = t;
                    a.onclick = (e) => { e.preventDefault(); changeTheme(t); };
                    optionsContainer.appendChild(a);
                });
            } catch (e) { document.getElementById('theme-selected-text').textContent = "NEON_V2"; }
        }

        function changeTheme(newTheme) {
            fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme: newTheme }) })
            .then(() => location.reload()); 
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
                    const a = document.createElement('a');
                    a.href = '#';
                    a.className = 'block px-4 py-3 text-xs text-white hover:bg-[#00f3ff]/10 transition-all border-b border-white/5';
                    a.textContent = cat;
                    a.onclick = (e) => {
                        e.preventDefault();
                        document.getElementById('category-selected-text').textContent = cat;
                        document.getElementById('category').value = cat;
                    };
                    optionsContainer.appendChild(a);
                });
            } catch (e) { globalCategories = ['Media', 'System']; }
        }

        async function fetchServices() {
            try {
                const res = await fetch('/api/services');
                const services = await res.json();
                renderDashboard(services);
            } catch (e) {
                renderDashboard([
                    {id: 1, name: "PLEX_SERVER", desc: "4K Media Streaming", category: "Media", url: "#"},
                    {id: 2, name: "DOCKER_MGR", desc: "Container Management", category: "System", url: "#"}
                ]);
            }
        }

        function renderDashboard(services) {
            const container = document.getElementById('dynamic-content');
            container.innerHTML = '';
            const grouped = {};
            globalCategories.forEach(cat => grouped[cat] = []); 
            services.forEach(srv => {
                if (grouped[srv.category]) grouped[srv.category].push(srv);
            });

            for (const [category, items] of Object.entries(grouped)) {
                if (items.length === 0) continue;
                const section = document.createElement('section');
                section.className = 'mb-16';
                section.innerHTML = `
                    <h2 class="section-title mb-8 flex justify-between items-center group/cat">
                        <span>[ ${category} ]</span>
                        <button onclick="deleteCategory('${category}')" class="text-indigo-700 hover:text-red-500 opacity-0 group-hover/cat:opacity-100 transition text-[9px] font-black uppercase tracking-widest">Remove Group</button>
                    </h2>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        ${items.map(srv => `
                            <a href="${srv.url}" target="_blank" class="service-card p-6 rounded-lg block relative group/card">
                                <div class="text-[#00f3ff] font-black tracking-wider text-sm mb-1 uppercase">${srv.name}</div>
                                <div class="text-[10px] text-indigo-300 font-medium tracking-wide opacity-70">${srv.desc || 'NO_DESCRIPTION'}</div>
                                <div class="absolute bottom-0 left-0 h-0.5 w-0 bg-[#00f3ff] group-hover/card:w-full transition-all duration-500 shadow-[0_0_10px_#00f3ff]"></div>
                                <button onclick="deleteService(event, '${srv.id}')" class="absolute top-4 right-4 text-indigo-500 hover:text-[#ff00a0] opacity-0 group-hover/card:opacity-100 transition-opacity">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                                </button>
                            </a>
                        `).join('')}
                    </div>
                `;
                container.appendChild(section);
            }
        }

        // Logic functions remain the same as your provided code
        function addCategory() {
            const input = document.getElementById('new-category-name');
            const val = input.value.trim();
            if (!val) return;
            fetch('/api/categories', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: val }) })
            .then(() => { input.value = ''; document.getElementById('details-category').removeAttribute('open'); init(); });
        }

        function deleteCategory(catName) {
            if(confirm(`TERMINATE ${catName}?`)) fetch(`/api/categories/${encodeURIComponent(catName)}`, { method: 'DELETE' }).then(() => init());
        }

        function addService() {
            const newService = {
                name: document.getElementById('name').value, desc: document.getElementById('desc').value,
                url: document.getElementById('url').value, category: document.getElementById('category').value
            };
            if (!newService.name || !newService.url) { alert("ERROR: NAME_AND_URL_REQUIRED"); return; }
            fetch('/api/services', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newService) })
            .then(() => { 
                document.getElementById('name').value = ''; 
                document.getElementById('desc').value = ''; 
                document.getElementById('url').value = ''; 
                document.getElementById('details-service').removeAttribute('open'); 
                init(); 
            });
        }

        function deleteService(event, id) {
            event.preventDefault(); 
            if(confirm('PURGE SERVICE?')) fetch(`/api/services/${id}`, { method: 'DELETE' }).then(() => init());
        }
        init();
    </script>
</body>
</html>"""

def setup_environment():
   # Create necessary directories
    for d in [DATA_DIR, IMAGES_DIR, TEMPLATES_DIR]:
        os.makedirs(d, exist_ok=True)
    
    # Initialize JSON data files if they don't exist
    if not os.path.exists(SERVICES_FILE):
        with open(SERVICES_FILE, 'w') as f: json.dump([], f)
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'w') as f: json.dump(DEFAULT_CATEGORIES, f)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f: json.dump(DEFAULT_CONFIG, f)

    # Create Default Theme File
    default_html_path = os.path.join(TEMPLATES_DIR, 'default.html')
    if not os.path.exists(default_html_path):
        with open(default_html_path, 'w') as f:
            f.write(DEFAULT_HTML)

    # Create Neon Theme File
    neon_html_path = os.path.join(TEMPLATES_DIR, 'neon.html')
    if not os.path.exists(neon_html_path):
        with open(neon_html_path, 'w') as f:
            f.write(NEON_HTML)
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

@app.route('/api/themes', methods=['GET'])
def get_themes():
    themes = [f.replace('.html', '') for f in os.listdir(TEMPLATES_DIR) if f.endswith('.html')]
    return jsonify(themes)

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