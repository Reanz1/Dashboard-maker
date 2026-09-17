/* ── Dashboard JS ── */

let globalCategories = [];
let globalServices = [];
let globalStatus = {};

// Set to a service id while the panel is editing that service, null while adding.
let editingServiceId = null;

// Icon chosen in the service panel, carried until the service is saved.
let editingIconUrl = '';

// Current text in the filter box.
let serviceFilter = '';

// Service values land in markup, so they have to be escaped: a name with a
// quote used to break the surrounding attribute and swallow its button.
function escapeHtml(value) {
    return String(value == null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

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
            // Close theme editor overlay when another panel opens
            if (detail !== detailsThemeEdit) closeThemeEditorOverlay();

            // Theme editor uses a body-level overlay instead of inline panel
            if (detail === detailsThemeEdit) {
                detail.removeAttribute('open');
                loadThemeCode().then(() => openThemeEditorOverlay());
                return;
            }

            const animatedChild = detail.querySelector('.animate-drop-fade');
            if (animatedChild) {
                animatedChild.classList.remove('animate-drop-fade');
                void animatedChild.offsetWidth;
                animatedChild.classList.add('animate-drop-fade');
            }
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
        closeThemeEditorOverlay();
    }

    // Cards are only draggable while arranging.
    const editing = document.body.classList.contains('edit-mode');
    document.querySelectorAll('.service-card').forEach(card => { card.draggable = editing; });
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

    fetchStatus();
    setInterval(fetchStatus, 60000);
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

// ── Theme Editor Overlay ──
// Moves the editor panel to a body-level overlay (like showConfirm)
// so it escapes all ancestor stacking contexts and containing blocks.
function openThemeEditorOverlay() {
    closeThemeEditorOverlay();
    const panel = detailsThemeEdit.querySelector('.editor-panel--full');
    if (!panel) return;

    const overlay = document.createElement('div');
    overlay.id = 'theme-editor-overlay';
    overlay.className = 'confirm-overlay';
    overlay.style.zIndex = '9000';

    // Move panel into the overlay; override positioning (overlay handles centering)
    panel.style.position = 'relative';
    panel.style.inset = 'auto';
    panel.style.margin = '0';
    panel.style.zIndex = 'auto';
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    // Replay fade-in
    panel.classList.remove('animate-drop-fade');
    void panel.offsetWidth;
    panel.classList.add('animate-drop-fade');

    // Close on backdrop click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeThemeEditorOverlay();
    });
}

function closeThemeEditorOverlay() {
    const overlay = document.getElementById('theme-editor-overlay');
    if (!overlay) return;
    const panel = overlay.querySelector('.editor-panel--full');
    if (panel) {
        panel.style.position = '';
        panel.style.inset = '';
        panel.style.margin = '';
        panel.style.zIndex = '';
        // Move panel back into the details element
        const summary = detailsThemeEdit.querySelector('summary');
        summary.insertAdjacentElement('afterend', panel);
    }
    overlay.remove();
}

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
        // Don't reset the picker out from under an edit in progress.
        if (globalCategories.length > 0 && editingServiceId === null) {
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
    const input = document.getElementById('new-category-name');
    const val = input.value.trim();
    if (!val) return;
    fetch('/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: val })
    }).then(() => {
        input.value = '';
        refresh();
    });
});

// ── Services ──
async function fetchServices() {
    try {
        const res = await fetch('/api/services');
        globalServices = await res.json();
        renderDashboard(globalServices);
    } catch (e) { console.error('Failed to fetch services:', e); }
}

document.getElementById('btn-add-service').addEventListener('click', () => {
    const service = {
        name: document.getElementById('svc-name').value,
        desc: document.getElementById('svc-desc').value,
        url: document.getElementById('svc-url').value,
        category: document.getElementById('category').value
    };
    if (!service.name || !service.url) return;

    service.icon = editingIconUrl;

    const editing = editingServiceId !== null;
    fetch(editing ? `/api/services/${editingServiceId}` : '/api/services', {
        method: editing ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(service)
    }).then(() => {
        detailsService.removeAttribute('open');
        resetServiceForm();
        refresh();
    });
});

// Re-read the data and repaint. Service and category actions go through this
// instead of reloading the page, so the dashboard no longer flashes on save.
async function refresh() {
    await fetchCategories();
    await fetchServices();
}

// ── Edit Service ──
// Editing reuses the "Add Service" panel rather than adding markup of its own:
// every theme is a standalone HTML file, and user themes are copies frozen in
// /data/themes, so a new element would simply be missing from existing themes.

// The panel's "add" wording, captured before editing ever overwrites it.
const addServiceLabels = {
    button: document.getElementById('btn-add-service').textContent,
    summary: (detailsService.querySelector('summary') || {}).textContent || '+ Add Service'
};

function startEditingService(srv) {
    editingServiceId = srv.id;

    document.getElementById('svc-name').value = srv.name || '';
    document.getElementById('svc-desc').value = srv.desc || '';
    document.getElementById('svc-url').value = srv.url || '';
    setSelectedCategory(srv.category || '');
    setEditingIcon(srv.icon || '');

    document.getElementById('btn-add-service').textContent = 'Save Changes';
    const summary = detailsService.querySelector('summary');
    if (summary) summary.textContent = 'Edit Service';

    detailsService.setAttribute('open', '');
    document.getElementById('svc-name').focus();
}

function resetServiceForm() {
    editingServiceId = null;

    ['svc-name', 'svc-desc', 'svc-url'].forEach(id => {
        document.getElementById(id).value = '';
    });
    setSelectedCategory(globalCategories[0] || '');
    setEditingIcon('');

    document.getElementById('btn-add-service').textContent = addServiceLabels.button;
    const summary = detailsService.querySelector('summary');
    if (summary) summary.textContent = addServiceLabels.summary;
}

function setSelectedCategory(category) {
    document.getElementById('category').value = category;
    const label = document.getElementById('category-selected-text');
    if (label) label.textContent = category || 'Select Category...';
}

// ── Service Icons ──
// The panel's icon row is built here rather than in the themes, so that themes
// already cloned into /data/themes gain it without being touched.
(function buildIconPicker() {
    const row = document.createElement('div');
    row.className = 'svc-icon-row';
    row.innerHTML = `
        <div class="svc-icon-preview" id="svc-icon-preview"></div>
        <div class="svc-icon-actions">
            <button type="button" class="svc-icon-btn" id="svc-icon-choose">Choose Icon</button>
            <button type="button" class="svc-icon-btn" id="svc-icon-clear">Clear</button>
        </div>
        <input type="file" id="svc-icon-file" accept="image/*" hidden>
    `;
    document.getElementById('svc-url').insertAdjacentElement('afterend', row);

    const fileInput = document.getElementById('svc-icon-file');
    document.getElementById('svc-icon-choose').addEventListener('click', () => fileInput.click());
    document.getElementById('svc-icon-clear').addEventListener('click', () => setEditingIcon(''));

    fileInput.addEventListener('change', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        const body = new FormData();
        body.append('file', file);
        try {
            const res = await fetch('/api/images', { method: 'POST', body });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || `Server returned ${res.status}`);
            setEditingIcon(data.url);
        } catch (err) {
            showConfirm('Upload Failed', escapeHtml(err.message), () => {});
        }
        fileInput.value = '';  // let the same file be picked again
    });

    setEditingIcon('');
})();

function setEditingIcon(url) {
    editingIconUrl = url || '';
    const preview = document.getElementById('svc-icon-preview');
    if (!preview) return;

    preview.innerHTML = editingIconUrl
        ? `<img src="${escapeHtml(editingIconUrl)}" alt="">`
        : '<span class="svc-icon-empty">No icon</span>';
}

// Leaving the panel drops the edit, so it reopens as "Add Service" next time.
detailsService.addEventListener('toggle', () => {
    if (!detailsService.open && editingServiceId !== null) resetServiceForm();
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

    const filter = serviceFilter.trim().toLowerCase();
    let matched = 0;

    for (const [category, items] of Object.entries(grouped)) {
        if (items.length === 0) continue;

        const visible = filter
            ? items.filter(srv => [srv.name, srv.desc, srv.url, srv.category]
                .some(field => String(field || '').toLowerCase().includes(filter)))
            : items;
        if (visible.length === 0) continue;
        matched += visible.length;

        const section = document.createElement('section');
        section.className = 'mb-12';

        const title = document.createElement('h2');
        title.className = 'section-title mb-6 group/cat';
        // "Other" is the bucket for services whose category is gone, not a
        // real category, so it can't be renamed or removed.
        const isRealCategory = globalCategories.includes(category);
        title.innerHTML = `
            <span>${escapeHtml(category)}</span>
            ${isRealCategory ? `
            <button class="edit-mode-only cat-rename-btn" data-rename-category="${escapeHtml(category)}">Rename</button>
            <button class="edit-mode-only cat-delete-btn" data-delete-category="${escapeHtml(category)}">Remove</button>` : ''}
        `;
        section.appendChild(title);

        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4';

        visible.forEach(srv => {
            let link = srv.url;
            if (link && !link.startsWith('http')) link = 'http://' + link;

            const card = document.createElement('a');
            card.href = link;
            card.target = '_blank';
            card.className = 'service-card p-5 block relative group/card';
            card.dataset.serviceId = srv.id;
            card.dataset.category = category;
            // Reordering is a drag, so cards only become draggable in edit mode.
            card.draggable = document.body.classList.contains('edit-mode');

            const state = globalStatus[srv.id];
            card.innerHTML = `
                <div class="relative card-body">
                    ${srv.icon ? `<img class="card-icon" src="${escapeHtml(srv.icon)}" alt="">` : ''}
                    <div class="card-text">
                        <div class="card-title">
                            <span class="status-dot status-${state || 'unknown'}" title="${
                                state === 'up' ? 'Reachable' : state === 'down' ? 'Not reachable' : 'Checking...'
                            }"></span>${escapeHtml(srv.name)}
                        </div>
                        <div class="card-desc">${escapeHtml(srv.desc || '')}</div>
                    </div>
                </div>
                <button class="edit-mode-only card-edit-btn" data-edit-service="${escapeHtml(srv.id)}" title="Edit">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M12 20h9"></path>
                        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z"></path>
                    </svg>
                </button>
                <button class="edit-mode-only card-delete-btn" data-delete-service="${escapeHtml(srv.id)}" title="Remove">
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

    if (filter && matched === 0) {
        const empty = document.createElement('p');
        empty.className = 'filter-empty';
        empty.textContent = `Nothing matches "${serviceFilter}"`;
        container.appendChild(empty);
    }
}

// ── Event Delegation for dynamic content ──
document.getElementById('dynamic-content').addEventListener('click', (e) => {
    const editServiceBtn = e.target.closest('[data-edit-service]');
    if (editServiceBtn) {
        e.preventDefault();
        const srv = globalServices.find(s => s.id === editServiceBtn.dataset.editService);
        if (srv) startEditingService(srv);
        return;
    }

    const deleteServiceBtn = e.target.closest('[data-delete-service]');
    if (deleteServiceBtn) {
        e.preventDefault();
        const id = deleteServiceBtn.dataset.deleteService;
        showConfirm('Remove Service?', 'This service will be removed from the dashboard.', () => {
            fetch(`/api/services/${id}`, { method: 'DELETE' }).then(() => refresh());
        });
        return;
    }

    const renameCatBtn = e.target.closest('[data-rename-category]');
    if (renameCatBtn) {
        e.preventDefault();
        renameCategory(renameCatBtn.dataset.renameCategory);
        return;
    }

    const deleteCatBtn = e.target.closest('[data-delete-category]');
    if (deleteCatBtn) {
        e.preventDefault();
        deleteCategory(deleteCatBtn.dataset.deleteCategory);
        return;
    }

    // In edit mode a card is a thing you arrange, not a link you follow.
    if (document.body.classList.contains('edit-mode') && e.target.closest('.service-card')) {
        e.preventDefault();
    }
});

// ── Category Rename / Delete ──
function renameCategory(category) {
    showPrompt('Rename Category', 'New name for this category:', category, async (newName) => {
        const trimmed = newName.trim();
        if (!trimmed || trimmed === category) return;

        const res = await fetch(`/api/categories/${encodeURIComponent(category)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: trimmed })
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            showConfirm('Rename Failed', escapeHtml(data.error || `Server returned ${res.status}`), () => {});
            return;
        }
        refresh();
    });
}

function deleteCategory(category) {
    const affected = globalServices.filter(s => s.category === category);
    const targets = globalCategories.filter(c => c !== category);

    // With nothing inside it, removing a category needs no discussion.
    if (affected.length === 0) {
        showConfirm('Remove Category?', `The <strong>"${escapeHtml(category)}"</strong> category will be removed.`, () => {
            fetch(`/api/categories/${encodeURIComponent(category)}`, { method: 'DELETE' }).then(() => refresh());
        });
        return;
    }

    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = `
        <div class="confirm-box">
            <h3>Remove Category?</h3>
            <p>
                <strong>${escapeHtml(category)}</strong> still holds
                ${affected.length} service${affected.length === 1 ? '' : 's'}.
                Where should ${affected.length === 1 ? 'it' : 'they'} go?
            </p>
            <select class="panel-input reassign-select">
                ${targets.map(c => `<option value="${escapeHtml(c)}">Move to "${escapeHtml(c)}"</option>`).join('')}
                <option value="">Leave them uncategorised</option>
            </select>
            <div class="confirm-actions" style="margin-top:1.5rem">
                <button type="button" class="btn-secondary confirm-cancel">Cancel</button>
                <button type="button" class="btn-primary confirm-ok">Remove</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    const close = () => overlay.remove();
    overlay.querySelector('.confirm-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    overlay.querySelector('.confirm-ok').addEventListener('click', () => {
        const target = overlay.querySelector('.reassign-select').value;
        close();
        const query = target ? `?reassign=${encodeURIComponent(target)}` : '';
        fetch(`/api/categories/${encodeURIComponent(category)}${query}`, { method: 'DELETE' })
            .then(() => refresh());
    });
}

// A themed stand-in for window.prompt, built from the confirm dialog's classes.
function showPrompt(title, message, initial, onSubmit) {
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = `
        <div class="confirm-box">
            <h3>${escapeHtml(title)}</h3>
            <p>${escapeHtml(message)}</p>
            <input type="text" class="panel-input prompt-input" value="${escapeHtml(initial)}">
            <div class="confirm-actions" style="margin-top:1.5rem">
                <button type="button" class="btn-secondary confirm-cancel">Cancel</button>
                <button type="button" class="btn-primary confirm-ok">Save</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    const input = overlay.querySelector('.prompt-input');
    input.focus();
    input.select();

    const close = () => overlay.remove();
    const submit = () => { const v = input.value; close(); onSubmit(v); };

    overlay.querySelector('.confirm-cancel').addEventListener('click', close);
    overlay.querySelector('.confirm-ok').addEventListener('click', submit);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submit();
        if (e.key === 'Escape') close();
    });
}

// ── Drag to Reorder ──
// Stored order is display order, so a drop just re-sends the ids in their new
// sequence. Dragging is confined to edit mode and to one category at a time.
let draggedCard = null;

const dynamicContent = document.getElementById('dynamic-content');

dynamicContent.addEventListener('dragstart', (e) => {
    const card = e.target.closest('.service-card');
    if (!card || !document.body.classList.contains('edit-mode')) return;
    // A filtered grid is only part of the list; reordering it would move the
    // hidden cards too, so dragging waits until the filter is cleared.
    if (serviceFilter.trim()) { e.preventDefault(); return; }
    draggedCard = card;
    card.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    // Firefox only starts a drag once something is on the dataTransfer.
    e.dataTransfer.setData('text/plain', card.dataset.serviceId);
});

dynamicContent.addEventListener('dragover', (e) => {
    if (!draggedCard) return;
    const over = e.target.closest('.service-card');
    if (!over || over === draggedCard) return;
    if (over.dataset.category !== draggedCard.dataset.category) return;

    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    // Insert before or after depending on which half was entered.
    const box = over.getBoundingClientRect();
    const after = (e.clientX - box.left) > box.width / 2;
    over.parentNode.insertBefore(draggedCard, after ? over.nextSibling : over);
});

dynamicContent.addEventListener('drop', (e) => {
    if (!draggedCard) return;
    e.preventDefault();
    persistOrder();
});

dynamicContent.addEventListener('dragend', () => {
    if (draggedCard) draggedCard.classList.remove('dragging');
    draggedCard = null;
});

function persistOrder() {
    const order = [...dynamicContent.querySelectorAll('.service-card')]
        .map(card => card.dataset.serviceId);

    // Keep the local copy in step so the next render doesn't undo the drag.
    const byId = new Map(globalServices.map(s => [s.id, s]));
    globalServices = order.map(id => byId.get(id)).filter(Boolean)
        .concat(globalServices.filter(s => !order.includes(s.id)));

    fetch('/api/services/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order })
    });
}

// ── Service Status ──
async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        globalStatus = await res.json();
        applyStatus();
    } catch (e) { console.error('Failed to fetch status:', e); }
}

// Repaint just the dots, so a status sweep never disturbs a drag or a filter.
function applyStatus() {
    document.querySelectorAll('.service-card').forEach(card => {
        const dot = card.querySelector('.status-dot');
        if (!dot) return;
        const state = globalStatus[card.dataset.serviceId] || 'unknown';
        dot.className = `status-dot status-${state}`;
        dot.title = state === 'up' ? 'Reachable'
            : state === 'down' ? 'Not reachable' : 'Checking...';
    });
}

// ── Search ──
(function buildSearchBox() {
    const wrap = document.createElement('div');
    wrap.className = 'svc-search-wrap';
    wrap.innerHTML = `<input type="text" id="svc-search" class="svc-search" placeholder="Search services...">`;
    dynamicContent.parentNode.insertBefore(wrap, dynamicContent);

    document.getElementById('svc-search').addEventListener('input', (e) => {
        serviceFilter = e.target.value;
        renderDashboard(globalServices);
    });
})();

// ── Styles for everything injected above ──
// Themes inline their own CSS and user themes are frozen copies, so new UI has
// to bring its styling with it, expressed in each theme's existing variables.
(function injectAddedStyles() {
    const style = document.createElement('style');
    style.textContent = `
.card-edit-btn {
    position: absolute;
    top: 1rem;
    right: calc(1rem + 14px + (2 * var(--card-delete-padding, 0px)) + var(--card-edit-gap, 0.5rem));
    color: var(--card-delete-color);
    opacity: 0;
    transition: all 0.2s;
    cursor: pointer;
    background: var(--card-delete-bg, transparent);
    border: var(--card-delete-border, none);
    padding: var(--card-delete-padding, 0);
    border-radius: var(--card-delete-radius, 0);
}
.card-edit-btn:hover {
    color: var(--card-edit-hover-color, #3b82f6);
    background: var(--card-edit-hover-bg, var(--card-delete-hover-bg, transparent));
}
.service-card:hover .card-edit-btn { opacity: 1; }

.cat-rename-btn {
    opacity: 0;
    transition: all 0.2s;
    margin-left: 0.5rem;
    font-size: var(--cat-delete-size, 0.75rem);
    font-weight: var(--cat-delete-weight, 400);
    color: var(--cat-delete-color);
    text-transform: var(--cat-delete-transform, lowercase);
    letter-spacing: var(--cat-delete-tracking, normal);
    background: var(--cat-delete-bg, transparent);
    border: var(--cat-delete-border, none);
    padding: var(--cat-delete-padding, 0);
    border-radius: var(--cat-delete-radius, 0);
    cursor: pointer;
}
.cat-rename-btn:hover { color: var(--card-edit-hover-color, #3b82f6); }
.section-title:hover .cat-rename-btn { opacity: 1; }

/* Icon + text sit side by side; without an icon the text is where it always was. */
.card-body { display: flex; align-items: center; gap: 0.875rem; }
.card-text { min-width: 0; flex: 1; }
.card-icon {
    width: var(--card-icon-size, 2.25rem);
    height: var(--card-icon-size, 2.25rem);
    object-fit: contain;
    border-radius: var(--card-icon-radius, 0.375rem);
    flex-shrink: 0;
}

.status-dot {
    display: inline-block;
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    margin-right: 0.5rem;
    vertical-align: middle;
    background: var(--status-unknown-color, #6b7280);
    transition: background 0.3s;
}
.status-up { background: var(--status-up-color, #22c55e); }
.status-down { background: var(--status-down-color, #ef4444); }

.svc-search-wrap { margin-bottom: 2rem; }
.svc-search {
    background: var(--input-bg);
    border: 1px solid var(--input-border);
    color: var(--input-text);
    padding: 0.625rem 0.875rem;
    border-radius: var(--input-radius, 0.25rem);
    font-size: 0.875rem;
    width: 100%;
    max-width: 22rem;
    outline: none;
    transition: border-color 0.2s;
}
.svc-search:focus { border-color: var(--input-focus-border); box-shadow: var(--input-focus-shadow, none); }
.filter-empty { color: var(--card-desc-color, #737373); font-size: 0.875rem; }

.svc-icon-row { display: flex; align-items: center; gap: 0.75rem; }
.svc-icon-preview {
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px dashed var(--input-border);
    border-radius: var(--input-radius, 0.25rem);
    overflow: hidden;
    flex-shrink: 0;
}
.svc-icon-preview img { width: 100%; height: 100%; object-fit: contain; }
.svc-icon-empty { font-size: 0.5625rem; color: var(--card-desc-color, #737373); text-align: center; }
.svc-icon-actions { display: flex; gap: 0.5rem; }
.svc-icon-btn {
    background: transparent;
    border: 1px solid var(--input-border);
    color: var(--btn-secondary-text, var(--toolbar-link-color));
    font-size: 0.75rem;
    padding: 0.375rem 0.75rem;
    border-radius: var(--input-radius, 0.25rem);
    cursor: pointer;
    transition: all 0.2s;
}
.svc-icon-btn:hover { border-color: var(--input-focus-border); color: var(--btn-secondary-hover-text, white); }

body.edit-mode .service-card { cursor: grab; }
.service-card.dragging { opacity: 0.4; cursor: grabbing; }
.reassign-select { cursor: pointer; }
`;
    document.head.appendChild(style);
})();

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
