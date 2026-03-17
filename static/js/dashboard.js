/* ── Dashboard JS ── */

let globalCategories = [];

const detailsService    = document.getElementById('details-service');
const detailsCategory   = document.getElementById('details-category');
const detailsThemeClone = document.getElementById('details-theme-clone');
const detailsThemeEdit  = document.getElementById('details-theme-edit');

const allDetails = [detailsService, detailsCategory, detailsThemeClone, detailsThemeEdit];

// Close other panels when one opens + replay animation
allDetails.forEach(detail => {
    detail.addEventListener('toggle', () => {
        if (detail.open) {
            allDetails.forEach(other => {
                if (other !== detail) other.removeAttribute('open');
            });
            const animatedChild = detail.querySelector('.animate-drop-fade');
            if (animatedChild) {
                animatedChild.classList.remove('animate-drop-fade');
                void animatedChild.offsetWidth;
                animatedChild.classList.add('animate-drop-fade');
            }
            if (detail === detailsThemeEdit) loadThemeCode();
        }
    });
});

// ── Edit Mode ──
document.getElementById('edit-mode-btn').addEventListener('click', () => {
    document.body.classList.toggle('edit-mode');
    const btn = document.getElementById('edit-mode-btn');
    const btnText = document.getElementById('edit-btn-text');

    if (document.body.classList.contains('edit-mode')) {
        btn.classList.add('active');
        if (btnText) btnText.textContent = btn.dataset.activeText || 'Editing';
    } else {
        btn.classList.remove('active');
        if (btnText) btnText.textContent = btn.dataset.idleText || 'Edit';
        allDetails.forEach(d => d.removeAttribute('open'));
    }
});

// ── Dropdown Toggle ──
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

// ── Init ──
async function init() {
    await fetchThemes();
    await fetchCategories();
    await fetchServices();
}

// ── Custom Confirmation Dialog ──
function showConfirm(title, message, onConfirm) {
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = `
        <div class="confirm-box">
            <h3>${title}</h3>
            <p>${message}</p>
            <div class="confirm-actions">
                <button type="button" class="btn-secondary confirm-cancel">Cancel</button>
                <button type="button" class="btn-primary confirm-ok">Confirm</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelector('.confirm-cancel').addEventListener('click', () => overlay.remove());
    overlay.querySelector('.confirm-ok').addEventListener('click', () => {
        overlay.remove();
        onConfirm();
    });
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.remove();
    });
}

// ── Themes ──
async function fetchThemes() {
    try {
        const [themesRes, configRes] = await Promise.all([fetch('/api/themes'), fetch('/api/config')]);
        const themes = await themesRes.json();
        const config = await configRes.json();

        document.getElementById('theme-selected-text').textContent = config.theme.toUpperCase() + ' THEME';
        document.getElementById('theme-selector').value = config.theme;

        const container = document.getElementById('theme-options');
        container.innerHTML = '';
        themes.forEach(t => {
            const a = document.createElement('a');
            a.href = '#';
            a.className = 'dropdown-item';
            a.textContent = t + ' Theme';
            a.addEventListener('click', (e) => { e.preventDefault(); changeTheme(t); });
            container.appendChild(a);
        });
    } catch (e) { console.error('Failed to fetch themes:', e); }
}

function changeTheme(newTheme) {
    fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: newTheme })
    }).then(() => location.reload());
}

// ── Clone Theme ──
document.getElementById('btn-clone-theme').addEventListener('click', () => {
    const val = document.getElementById('new-theme-name').value.trim();
    if (!val) return;
    fetch('/api/themes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: val })
    }).then(() => location.reload());
});

// ── Delete Theme ──
document.getElementById('btn-delete-theme').addEventListener('click', () => {
    const currentTheme = document.getElementById('theme-selector').value;
    if (['default', 'neon', 'ocean'].includes(currentTheme)) {
        showConfirm('Cannot Delete', 'Built-in themes cannot be deleted.', () => {});
        return;
    }
    showConfirm(
        'Delete Theme?',
        `Are you sure you want to delete the <strong>"${currentTheme}"</strong> theme?`,
        () => {
            fetch(`/api/themes/${currentTheme}`, { method: 'DELETE' }).then(res => {
                if (res.ok) location.reload();
            });
        }
    );
});

// ── Theme Editor (single HTML file) ──
let originalThemeHtml = '';

async function loadThemeCode() {
    const currentTheme = document.getElementById('theme-selector').value;
    const res = await fetch(`/api/themes/${currentTheme}`);
    const data = await res.json();
    document.getElementById('html-code-editor').value = data.content;
    originalThemeHtml = data.content;
}

document.getElementById('btn-save-theme-code').addEventListener('click', (e) => {
    const content = document.getElementById('html-code-editor').value;
    if (content === originalThemeHtml) {
        showConfirm('No Changes', 'No changes were detected.', () => {});
        return;
    }

    showConfirm(
        'Save Changes?',
        'This will update the theme file (HTML + CSS). If something breaks, use <strong>"Reset to Default"</strong> to restore the original.',
        async () => {
            const currentTheme = document.getElementById('theme-selector').value;
            const btn = e.target;
            const originalText = btn.innerText;
            btn.innerText = 'Saving...';

            try {
                const response = await fetch(`/api/themes/${currentTheme}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
                if (!response.ok) throw new Error(`Server returned ${response.status}`);
                location.reload();
            } catch (error) {
                showConfirm('Error', 'Failed to save changes.', () => {});
                btn.innerText = originalText;
            }
        }
    );
});

document.getElementById('btn-discard-theme-code').addEventListener('click', loadThemeCode);

document.getElementById('btn-reset-theme').addEventListener('click', () => {
    const currentTheme = document.getElementById('theme-selector').value;
    showConfirm(
        'Reset to Default?',
        `This will discard all customizations to the <strong>"${currentTheme}"</strong> theme and restore the original.`,
        async () => {
            try {
                const response = await fetch(`/api/themes/${currentTheme}/reset`, { method: 'POST' });
                if (!response.ok) throw new Error(`Server returned ${response.status}`);
                location.reload();
            } catch (error) {
                showConfirm('Error', 'Failed to reset theme.', () => {});
            }
        }
    );
});

// ── Categories ──
async function fetchCategories() {
    try {
        const res = await fetch('/api/categories');
        globalCategories = await res.json();
        const container = document.getElementById('category-options');
        container.innerHTML = '';
        if (globalCategories.length > 0) {
            document.getElementById('category-selected-text').textContent = globalCategories[0];
            document.getElementById('category').value = globalCategories[0];
        }
        globalCategories.forEach(cat => {
            const a = document.createElement('a');
            a.href = '#';
            a.className = 'category-item';
            a.textContent = cat;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                document.getElementById('category-selected-text').textContent = cat;
                document.getElementById('category').value = cat;
            });
            container.appendChild(a);
        });
    } catch (e) { console.error('Failed to fetch categories:', e); }
}

document.getElementById('btn-add-category').addEventListener('click', () => {
    const val = document.getElementById('new-category-name').value.trim();
    if (!val) return;
    fetch('/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: val })
    }).then(() => location.reload());
});

// ── Services ──
async function fetchServices() {
    try {
        const res = await fetch('/api/services');
        const services = await res.json();
        renderDashboard(services);
    } catch (e) { console.error('Failed to fetch services:', e); }
}

document.getElementById('btn-add-service').addEventListener('click', () => {
    const newService = {
        name: document.getElementById('svc-name').value,
        desc: document.getElementById('svc-desc').value,
        url: document.getElementById('svc-url').value,
        category: document.getElementById('category').value
    };
    if (!newService.name || !newService.url) return;
    fetch('/api/services', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newService)
    }).then(() => location.reload());
});

function renderDashboard(services) {
    const container = document.getElementById('dynamic-content');
    container.innerHTML = '';
    const grouped = {};
    globalCategories.forEach(cat => grouped[cat] = []);
    services.forEach(srv => {
        if (grouped[srv.category] !== undefined) {
            grouped[srv.category].push(srv);
        } else {
            if (!grouped['Other']) grouped['Other'] = [];
            grouped['Other'].push(srv);
        }
    });

    for (const [category, items] of Object.entries(grouped)) {
        if (items.length === 0) continue;

        const section = document.createElement('section');
        section.className = 'mb-12';

        const title = document.createElement('h2');
        title.className = 'section-title mb-6 group/cat';
        title.innerHTML = `
            <span>${category}</span>
            <button class="edit-mode-only cat-delete-btn" data-delete-category="${category}">Remove</button>
        `;
        section.appendChild(title);

        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4';

        items.forEach(srv => {
            let link = srv.url;
            if (link && !link.startsWith('http')) link = 'http://' + link;

            const card = document.createElement('a');
            card.href = link;
            card.target = '_blank';
            card.className = 'service-card p-5 block relative group/card';
            card.innerHTML = `
                <div class="relative" style="z-index:1">
                    <div class="card-title">${srv.name}</div>
                    <div class="card-desc">${srv.desc || ''}</div>
                </div>
                <button class="edit-mode-only card-delete-btn" data-delete-service="${srv.id}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            `;
            grid.appendChild(card);
        });

        section.appendChild(grid);
        container.appendChild(section);
    }
}

// ── Event Delegation for dynamic content ──
document.getElementById('dynamic-content').addEventListener('click', (e) => {
    const deleteServiceBtn = e.target.closest('[data-delete-service]');
    if (deleteServiceBtn) {
        e.preventDefault();
        const id = deleteServiceBtn.dataset.deleteService;
        showConfirm('Remove Service?', 'This service will be removed from the dashboard.', () => {
            fetch(`/api/services/${id}`, { method: 'DELETE' }).then(() => location.reload());
        });
        return;
    }

    const deleteCatBtn = e.target.closest('[data-delete-category]');
    if (deleteCatBtn) {
        e.preventDefault();
        const cat = deleteCatBtn.dataset.deleteCategory;
        showConfirm('Remove Category?', `The <strong>"${cat}"</strong> category will be removed.`, () => {
            fetch(`/api/categories/${encodeURIComponent(cat)}`, { method: 'DELETE' }).then(() => location.reload());
        });
    }
});

// ── Category dropdown button ──
document.getElementById('category-dropdown-btn').addEventListener('click', (e) => {
    toggleDropdown('category-dropdown', e);
});

// ── Theme dropdown button ──
document.getElementById('theme-dropdown-btn').addEventListener('click', (e) => {
    toggleDropdown('theme-dropdown', e);
});

// ── Go ──
init();
