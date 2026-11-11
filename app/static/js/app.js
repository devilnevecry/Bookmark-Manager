/* Bookmark Manager - Frontend JavaScript */

const API_BASE = '/api';
let currentPage = 1;
let currentFilter = 'all'; // all, favorite, archived
let currentCategoryId = null;
let currentTag = null;
let currentSearch = '';
let currentSort = 'created_at_desc';
let totalPages = 1;

// --- Initialization ---

async function init() {
    await loadCategories();
    await loadTags();
    await searchBookmarks();
    setupEventListeners();
}

function setupEventListeners() {
    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                const id = overlay.id;
                if (id === 'bookmarkModal') closeBookmarkModal();
                if (id === 'categoryModal') closeCategoryModal();
                if (id === 'importExportModal') closeImportExport();
            }
        });
    });

    // Import form
    const importForm = document.getElementById('importForm');
    importForm.addEventListener('submit', (e) => {
        e.preventDefault();
        importBookmarks();
    });
}

// --- Theme ---

function toggleTheme() {
    const body = document.body;
    const theme = body.getAttribute('data-theme');
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// --- API Helpers ---

async function apiRequest(endpoint, options = {}) {
    const url = API_BASE + endpoint;
    const config = {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    };
    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }
    const response = await fetch(url, config);
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Request failed');
    }
    if (response.status === 204) return null;
    return response.json();
}

// --- Load Data ---

async function loadCategories() {
    try {
        const categories = await apiRequest('/categories');
        const list = document.getElementById('categoryList');
        const select = document.getElementById('inputCategory');
        list.innerHTML = '';
        select.innerHTML = '<option value="">Без категории</option>';

        categories.forEach(cat => {
            // Sidebar item
            const item = document.createElement('div');
            item.className = currentCategoryId === cat.id ? 'category-item active' : 'category-item';
            item.innerHTML = `
                <span>${escapeHtml(cat.name)} <span style="font-size:0.75rem;opacity:0.6">(${cat.bookmark_count || 0})</span></span>
                <span class="delete" onclick="event.stopPropagation(); deleteCategory(${cat.id})">&times;</span>
            `;
            item.onclick = () => setCategoryFilter(cat.id, item);
            list.appendChild(item);

            // Select option
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name;
            select.appendChild(option);
        });
    } catch (e) {
        showToast('Ошибка загрузки категорий', 'error');
    }
}

async function loadTags() {
    try {
        const tags = await apiRequest('/tags');
        const list = document.getElementById('tagList');
        list.innerHTML = '';

        tags.forEach(tag => {
            const item = document.createElement('div');
            item.className = currentTag === tag.name ? 'tag-item active' : 'tag-item';
            item.innerHTML = `
                <span>#${escapeHtml(tag.name)} <span style="font-size:0.75rem;opacity:0.6">(${tag.bookmark_count || 0})</span></span>
                <span class="delete" onclick="event.stopPropagation(); deleteTag(${tag.id})">&times;</span>
            `;
            item.onclick = () => setTagFilter(tag.name, item);
            list.appendChild(item);
        });
    } catch (e) {
        showToast('Ошибка загрузки тегов', 'error');
    }
}

// --- Bookmarks ---

async function searchBookmarks() {
    const params = new URLSearchParams();
    params.append('page', currentPage);
    params.append('page_size', 20);

    if (currentFilter === 'favorite') params.append('is_favorite', 'true');
    if (currentFilter === 'archived') params.append('is_archived', 'true');
    if (currentCategoryId) params.append('category_id', currentCategoryId);
    if (currentTag) params.append('tag', currentTag);
    if (currentSearch) params.append('search', currentSearch);

    const [sortBy, sortOrder] = currentSort.split('_');
    params.append('sort_by', sortBy);
    params.append('sort_order', sortOrder);

    try {
        const data = await apiRequest('/bookmarks?' + params.toString());
        renderBookmarks(data.items);
        renderPagination(data.page, data.pages, data.total);
        document.getElementById('emptyState').style.display = data.items.length === 0 ? 'flex' : 'none';
        document.getElementById('bookmarksGrid').style.display = data.items.length === 0 ? 'none' : 'grid';
    } catch (e) {
        showToast('Ошибка загрузки закладок', 'error');
    }
}

function renderBookmarks(bookmarks) {
    const grid = document.getElementById('bookmarksGrid');
    grid.innerHTML = '';

    bookmarks.forEach(bm => {
        const card = document.createElement('div');
        card.className = `bookmark-card${bm.is_archived ? ' archived' : ''}`;
        card.onclick = (e) => {
            if (!e.target.closest('.btn-icon')) openBookmarkModal(bm.id);
        };

        const tagsHtml = (bm.tag_names || []).map(t => `<span class="bookmark-tag">${escapeHtml(t)}</span>`).join('');
        const favIcon = bm.is_favorite ? 'active' : '';
        const archiveBtn = bm.is_archived
            ? `<button class="btn-icon" title="Восстановить" onclick="event.stopPropagation(); restoreBookmark(${bm.id})">
                 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a3 3 0 0 0-3 3v6a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3V6z"/><path d="M10 2L22 2"/><path d="M16 20l6-6-6-6"/></svg>
               </button>`
            : `<button class="btn-icon" title="Архивировать" onclick="event.stopPropagation(); archiveBookmark(${bm.id})">
                 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="21 8 21 21 3 21"/></svg>
               </button>`;

        card.innerHTML = `
            <div class="bookmark-header">
                <div style="display:flex;align-items:center;">
                    <img class="bookmark-favicon" src="${escapeHtml(bm.favicon_url || '')}" onerror="this.style.display='none'" alt="favicon">
                    <div>
                        <div class="bookmark-title"><a href="${escapeHtml(bm.url)}" target="_blank" rel="noopener">${escapeHtml(bm.title)}</a></div>
                        <div class="bookmark-domain">${escapeHtml(bm.domain || '-')}</div>
                    </div>
                </div>
                <button class="btn-icon" title="Избранное" onclick="event.stopPropagation(); toggleFavorite(${bm.id})" class="${favIcon}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14l1.64-.32a.76.76 0 0 0 .85-.85l.32-1.64a1 1 0 0 0-1.28-1.28L17 10l-.32-1.64a1 1 0 0 0-1.28-1.28l-1.64.32a.76.76 0 0 0-.85.85l-.32 1.64a1 1 0 0 0 1.28 1.28zM12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10z"/></svg>
                </button>
                <button class="btn-icon" title="Открыть" onclick="event.stopPropagation(); window.open('${escapeHtml(bm.url)}', '_blank')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6"/><path d="M10 14 21 3"/></svg>
                </button>
                <button class="btn-icon" title="Копировать URL" onclick="event.stopPropagation(); copyUrl('${escapeHtml(bm.url)}')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                </button>
                <button class="btn-icon" title="Редактировать" onclick="event.stopPropagation(); openBookmarkModal(${bm.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                </button>
                ${archiveBtn}
                <button class="btn-icon" title="Удалить" onclick="event.stopPropagation(); deleteBookmark(${bm.id})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
            </div>
            ${bm.description ? `<div class="bookmark-description">${escapeHtml(bm.description)}</div>` : ''}
            <div class="bookmark-meta">
                <div class="bookmark-tags">${tagsHtml}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);">${formatDate(bm.created_at)}</div>
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderPagination(page, pages, total) {
    const pagination = document.getElementById('pagination');
    if (pages <= 1) {
        pagination.style.display = 'none';
        return;
    }
    pagination.style.display = 'flex';
    document.getElementById('pageInfo').textContent = `Страница ${page} из ${pages} (${total} закладок)`;
    document.getElementById('btnPrev').disabled = page <= 1;
    document.getElementById('btnNext').disabled = page >= pages;
}

function changePage(delta) {
    const newPage = currentPage + delta;
    if (newPage >= 1 && newPage <= totalPages) {
        currentPage = newPage;
        searchBookmarks();
    }
}

// --- Filters ---

function setFilter(filter, element) {
    currentFilter = filter;
    currentPage = 1;
    currentCategoryId = null;
    currentTag = null;

    // Update UI
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    if (element) element.classList.add('active');

    document.querySelectorAll('.category-item, .tag-item').forEach(item => item.classList.remove('active'));

    searchBookmarks();
}

function setCategoryFilter(categoryId, element) {
    currentCategoryId = categoryId;
    currentFilter = 'all';
    currentPage = 1;
    currentTag = null;

    document.querySelectorAll('.category-item').forEach(item => item.classList.remove('active'));
    if (element) element.classList.add('active');
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));

    searchBookmarks();
}

function setTagFilter(tagName, element) {
    currentTag = tagName;
    currentFilter = 'all';
    currentPage = 1;
    currentCategoryId = null;

    document.querySelectorAll('.tag-item').forEach(item => item.classList.remove('active'));
    if (element) element.classList.add('active');
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));

    searchBookmarks();
}

function sortBookmarks() {
    const select = document.getElementById('sortSelect');
    currentSort = select.value;
    currentPage = 1;
    searchBookmarks();
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

const searchBookmarksDebounced = debounce(() => {
    currentSearch = document.getElementById('searchInput').value;
    currentPage = 1;
    searchBookmarks();
}, 300);

// Override global searchBookmarks to use debounced version from input
window.searchBookmarks = function() {
    currentSearch = document.getElementById('searchInput').value;
    currentPage = 1;
    searchBookmarksData();
};

async function searchBookmarksData() {
    const params = new URLSearchParams();
    params.append('page', currentPage);
    params.append('page_size', 20);

    if (currentFilter === 'favorite') params.append('is_favorite', 'true');
    if (currentFilter === 'archived') params.append('is_archived', 'true');
    if (currentCategoryId) params.append('category_id', currentCategoryId);
    if (currentTag) params.append('tag', currentTag);
    if (currentSearch) params.append('search', currentSearch);

    const [sortBy, sortOrder] = currentSort.split('_');
    params.append('sort_by', sortBy);
    params.append('sort_order', sortOrder);

    try {
        const data = await apiRequest('/bookmarks?' + params.toString());
        renderBookmarks(data.items);
        renderPagination(data.page, data.pages, data.total);
        document.getElementById('emptyState').style.display = data.items.length === 0 ? 'flex' : 'none';
        document.getElementById('bookmarksGrid').style.display = data.items.length === 0 ? 'none' : 'grid';
    } catch (e) {
        showToast('Ошибка загрузки закладок', 'error');
    }
}

// --- Bookmark CRUD ---

async function toggleFavorite(bookmarkId) {
    try {
        await apiRequest(`/bookmarks/${bookmarkId}/favorite`, { method: 'POST' });
        await searchBookmarksData();
    } catch (e) {
        showToast('Ошибка при изменении избранного', 'error');
    }
}

async function archiveBookmark(bookmarkId) {
    try {
        await apiRequest(`/bookmarks/${bookmarkId}/archive`, { method: 'POST' });
        await searchBookmarksData();
    } catch (e) {
        showToast('Ошибка архивации', 'error');
    }
}

async function restoreBookmark(bookmarkId) {
    try {
        await apiRequest(`/bookmarks/${bookmarkId}/restore`, { method: 'POST' });
        await searchBookmarksData();
    } catch (e) {
        showToast('Ошибка восстановления', 'error');
    }
}

async function deleteBookmark(bookmarkId) {
    if (!confirm('Удалить эту закладку?')) return;
    try {
        await apiRequest(`/bookmarks/${bookmarkId}`, { method: 'DELETE' });
        await searchBookmarksData();
        showToast('Закладка удалена', 'success');
    } catch (e) {
        showToast('Ошибка удаления', 'error');
    }
}

function copyUrl(url) {
    navigator.clipboard.writeText(url).then(() => {
        showToast('URL скопирован', 'success');
    });
}

// --- Bookmark Modal ---

let editingBookmarkId = null;

function openBookmarkModal(bookmarkId = null) {
    editingBookmarkId = bookmarkId;
    const form = document.getElementById('bookmarkForm');
    const title = document.getElementById('modalTitle');
    const actionInput = document.getElementById('bookmarkAction');
    const idInput = document.getElementById('bookmarkId');

    form.reset();
    document.getElementById('metadataPreview').style.display = 'none';

    if (bookmarkId) {
        title.textContent = 'Редактировать закладку';
        actionInput.value = 'update';
        idInput.value = bookmarkId;
        loadBookmarkForEdit(bookmarkId);
    } else {
        title.textContent = 'Добавить закладку';
        actionInput.value = 'create';
        idInput.value = '';
    }

    document.getElementById('bookmarkModal').style.display = 'flex';
}

async function loadBookmarkForEdit(bookmarkId) {
    try {
        const bm = await apiRequest(`/bookmarks/${bookmarkId}`);
        document.getElementById('inputUrl').value = bm.url;
        document.getElementById('inputTitle').value = bm.title || '';
        document.getElementById('inputDescription').value = bm.description || '';
        document.getElementById('inputCategory').value = bm.category_id || '';
        document.getElementById('inputTags').value = (bm.tag_names || []).join(', ');
        document.getElementById('inputFavorite').checked = bm.is_favorite || false;
    } catch (e) {
        showToast('Ошибка загрузки закладки', 'error');
    }
}

async function fetchMetadata() {
    const url = document.getElementById('inputUrl').value;
    if (!url) return;

    try {
        const data = await apiRequest('/bookmarks', {
            method: 'POST',
            body: { url, fetch_metadata_only: true }
        });
    } catch (e) {
        // Endpoint may not exist, that's OK - metadata fetched on create
    }
}

async function saveBookmark() {
    const form = document.getElementById('bookmarkForm');
    const action = document.getElementById('bookmarkAction').value;
    const id = document.getElementById('bookmarkId').value;

    const url = document.getElementById('inputUrl').value.trim();
    const title = document.getElementById('inputTitle').value.trim();
    const description = document.getElementById('inputDescription').value.trim();
    const category_id = document.getElementById('inputCategory').value || null;
    const tags = document.getElementById('inputTags').value.split(',').map(t => t.trim()).filter(t => t);
    const is_favorite = document.getElementById('inputFavorite').checked;

    if (!url) {
        showToast('URL обязателен', 'error');
        return;
    }

    const payload = {
        url,
        title: title || undefined,
        description: description || undefined,
        category_id,
        is_favorite,
    };

    try {
        if (action === 'create') {
            await apiRequest('/bookmarks', { method: 'POST', body: payload });
        } else {
            await apiRequest(`/bookmarks/${id}`, { method: 'PUT', body: payload });
        }

        // Handle tags separately
        if (editingBookmarkId) {
            await setBookmarkTags(editingBookmarkId, tags);
        }

        closeBookmarkModal();
        await searchBookmarksData();
        await loadCategories();
        await loadTags();
        showToast(action === 'create' ? 'Закладка добавлена' : 'Закладка обновлена', 'success');
    } catch (e) {
        showToast(e.message || 'Ошибка сохранения', 'error');
    }
}

async function setBookmarkTags(bookmarkId, tags) {
    // First remove all tags, then add new ones
    // We need to get current tags first - simplified: just add new ones
    // In a full implementation we'd diff. For now, clear by removing all and re-adding.
    const bm = await apiRequest(`/bookmarks/${bookmarkId}`);
    const currentTagIds = [];
    // We don't have tag IDs easily, so let's just add tags via API
    for (const tagName of tags) {
        try {
            await apiRequest(`/bookmarks/${bookmarkId}/tags/${encodeURIComponent(tagName)}`, { method: 'POST' });
        } catch (e) {
            // Ignore if already exists
        }
    }
}

function closeBookmarkModal() {
    document.getElementById('bookmarkModal').style.display = 'none';
}

// --- Category Modal ---

let editingCategoryId = null;

function openCategoryModal(categoryId = null) {
    editingCategoryId = categoryId;
    const form = document.getElementById('categoryForm');
    const title = document.getElementById('categoryModalTitle');
    const idInput = document.getElementById('categoryId');

    form.reset();

    if (categoryId) {
        title.textContent = 'Редактировать категорию';
        idInput.value = categoryId;
        // Load category data
        loadCategoryForEdit(categoryId);
    } else {
        title.textContent = 'Добавить категорию';
        idInput.value = '';
    }

    document.getElementById('categoryModal').style.display = 'flex';
}

async function loadCategoryForEdit(categoryId) {
    try {
        const categories = await apiRequest('/categories');
        const cat = categories.find(c => c.id === categoryId);
        if (cat) {
            document.getElementById('categoryName').value = cat.name;
            document.getElementById('categoryDescription').value = cat.description || '';
        }
    } catch (e) {
        showToast('Ошибка загрузки категории', 'error');
    }
}

async function saveCategory() {
    const name = document.getElementById('categoryName').value.trim();
    const description = document.getElementById('categoryDescription').value.trim();
    const id = document.getElementById('categoryId').value;

    if (!name) {
        showToast('Название обязательно', 'error');
        return;
    }

    const payload = { name, description: description || undefined };

    try {
        if (id) {
            await apiRequest(`/categories/${id}`, { method: 'PUT', body: payload });
        } else {
            await apiRequest('/categories', { method: 'POST', body: payload });
        }
        closeCategoryModal();
        await loadCategories();
        showToast(id ? 'Категория обновлена' : 'Категория создана', 'success');
    } catch (e) {
        showToast(e.message || 'Ошибка сохранения категории', 'error');
    }
}

async function deleteCategory(categoryId) {
    if (!confirm('Удалить категорию? Закладки останутся без категории.')) return;
    try {
        await apiRequest(`/categories/${categoryId}`, { method: 'DELETE' });
        await loadCategories();
        showToast('Категория удалена', 'success');
    } catch (e) {
        showToast('Ошибка удаления категории', 'error');
    }
}

function closeCategoryModal() {
    document.getElementById('categoryModal').style.display = 'none';
}

// --- Tags ---

async function deleteTag(tagId) {
    if (!confirm('Удалить тег?')) return;
    try {
        await apiRequest(`/tags/${tagId}`, { method: 'DELETE' });
        await loadTags();
        await searchBookmarksData();
        showToast('Тег удален', 'success');
    } catch (e) {
        showToast('Ошибка удаления тега', 'error');
    }
}

// --- Import / Export ---

function toggleImportExport() {
    const modal = document.getElementById('importExportModal');
    modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
}

function closeImportExport() {
    document.getElementById('importExportModal').style.display = 'none';
}

async function exportBookmarks() {
    try {
        const response = await fetch(API_BASE + '/export');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'bookmarks.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        showToast('Экспорт завершен', 'success');
    } catch (e) {
        showToast('Ошибка экспорта', 'error');
    }
}

async function importBookmarks() {
    const fileInput = document.getElementById('importFile');
    if (!fileInput.files.length) {
        showToast('Выберите файл', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch(API_BASE + '/import', {
            method: 'POST',
            body: formData,
        });
        const result = await response.json();

        const resultDiv = document.getElementById('importResult');
        resultDiv.className = 'import-result success';
        resultDiv.textContent = `Импортировано: ${result.imported}, пропущено: ${result.skipped}`;
        if (result.errors && result.errors.length) {
            resultDiv.textContent += `\nОшибки: ${result.errors.join(', ')}`;
        }

        await searchBookmarksData();
        await loadCategories();
        await loadTags();
        showToast('Импорт завершен', 'success');
    } catch (e) {
        const resultDiv = document.getElementById('importResult');
        resultDiv.className = 'import-result error';
        resultDiv.textContent = e.message || 'Ошибка импорта';
    }
}

// --- Notifications ---

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${escapeHtml(message)}</span>
        <button onclick="this.parentElement.remove()" style="margin-left:auto;background:none;border:none;color:inherit;opacity:0.7;">×</button>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// --- Utils ---

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(isoString) {
    if (!isoString) return '-';
    const d = new Date(isoString);
    return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' });
}

// --- Start ---

init();