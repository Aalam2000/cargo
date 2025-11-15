// web/static/js/base.js
window.getCsrf = function () {
    const name = 'csrftoken=';
    const cookies = document.cookie.split(';').map(s => s.trim());
    for (const c of cookies) if (c.startsWith(name)) return c.substring(name.length);

    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
};

// Минимальная, проверенная реализация: TableSettings (auto-init).
(function () {
    const API_URL = '/api/table_settings/';

    function qs(root, sel) {
        return (root || document).querySelector(sel);
    }

    function qsa(root, sel) {
        return Array.from((root || document).querySelectorAll(sel));
    }

    function slug(s) {
        return String(s || '').trim().toLowerCase().replace(/\s+/g, '_').replace(/[^\w\-]/g, '');
    }

    async function fetchJson(url, opts) {
        const r = await fetch(url, opts);
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
    }

    // === Универсальная функция открытия модалок ===
    function openModal({ html = null, modalName = '', closable = true, onClose = null } = {}) {
      // если передан селектор/элемент DOM вместо html — поддержим оба варианта
      let modalEl;
      if (html instanceof HTMLElement) {
        modalEl = html;
      } else if (typeof html === 'string' && html.trim().startsWith('<')) {
        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        modalEl = wrapper.firstElementChild;
      }

      // если передан селектор (например '#paymentModal')
      if (!modalEl && typeof html === 'string') {
        modalEl = document.querySelector(html);
      }

      // если ничего не найдено — создаём пустую оболочку (ошибка вызывающему)
      if (!modalEl) {
        console.error('openModal: modal element not found / invalid html');
        return null;
      }

      // если modalEl уже в DOM и имеет .modal-overlay в корне — просто показать
      const existingOverlay = modalEl.closest('.modal-overlay');
      if (existingOverlay) {
        existingOverlay.classList.add('show');
        document.body.style.overflow = 'hidden';
        // навесим закрытие
        attachCloseHandlers(existingOverlay, modalEl, closable, onClose);
        return { overlay: existingOverlay, modal: modalEl, close: () => closeOverlay(existingOverlay, onClose) };
      }

      // иначе создаём overlay+modal и аппендим в body
      const overlay = document.createElement('div');
      overlay.className = 'modal-overlay show';
      if (modalName) overlay.dataset.modal = modalName;
      overlay.setAttribute('role', 'presentation');

      // если modalEl уже был в DOM — клонируем его (чтобы не убирать из места)
      const modalClone = modalEl.isConnected ? modalEl.cloneNode(true) : modalEl;
      modalClone.classList.add('modal', 'show');

      overlay.appendChild(modalClone);
      document.body.appendChild(overlay);
      document.body.style.overflow = 'hidden';

      attachCloseHandlers(overlay, modalClone, closable, onClose);

      return { overlay, modal: modalClone, close: () => closeOverlay(overlay, onClose) };

      // --- хелперы ---
      function attachCloseHandlers(overlayElem, modalElement, closableFlag, onCloseCb) {
        // клик вне модалки закрывает
        overlayElem.addEventListener('click', (e) => {
          if (!closableFlag) return;
          if (e.target === overlayElem) closeOverlay(overlayElem, onCloseCb);
        }, { once: false });

        // кнопки внутри
        modalElement.querySelectorAll('.modal-close, .btn-cancel, [data-modal-close]').forEach(btn => {
          btn.addEventListener('click', () => closeOverlay(overlayElem, onCloseCb));
        });

        // Escape
        const escHandler = (e) => { if (e.key === 'Escape' && closableFlag) closeOverlay(overlayElem, onCloseCb); };
        document.addEventListener('keydown', escHandler);
        // сохраняем ссылку чтобы удалить слушатель при закрытии
        overlayElem._escHandler = escHandler;
      }

      function closeOverlay(overlayElem, onCloseCb) {
        if (!overlayElem) return;
        overlayElem.classList.remove('show');
        // если overlay был добавлен динамически — удалить
        if (overlayElem.parentNode) overlayElem.parentNode.removeChild(overlayElem);
        document.body.style.overflow = '';
        if (overlayElem._escHandler) document.removeEventListener('keydown', overlayElem._escHandler);
        if (typeof onCloseCb === 'function') onCloseCb();
      }
    }

    window.openModal = openModal;

    function closeModal() {
        const m = qs(document, '#settings-modal');
        const o = qs(document, '#modal-overlay');
        if (m) m.classList.remove('show');
        if (o) o.classList.remove('show');
    }

    function readColumnsFromDOM(wrapper) {
        const ths = qsa(wrapper, 'table thead th');
        return ths.map((th, i) => ({
            key: th.dataset.colKey ? th.dataset.colKey : slug(th.textContent || ('col_' + i)),
            title: (th.textContent || '').trim(),
            visible: !(th.classList.contains('hidden') || th.style.display === 'none'),
            order: i
        }));
    }

    function applySettingsToDOM(wrapper, settings) {
        const table = qs(wrapper, 'table');
        if (!table) return;
        const thead = qs(table, 'thead');
        const tbody = qs(table, 'tbody');
        if (!thead || !tbody) return;
        const origThs = qsa(thead, 'th');
        const map = {};
        origThs.forEach((th, idx) => {
            const k = th.dataset.colKey ? th.dataset.colKey : slug(th.textContent || ('col_' + idx));
            map[k] = th;
        });
        const sorted = (settings.columns || []).slice().sort((a, b) => (a.order || 0) - (b.order || 0));
        const newHead = document.createElement('tr');
        sorted.forEach(c => {
            const th = map[c.key];
            if (th) {
                th.style.display = c.visible ? '' : 'none';
                if (c.visible) th.classList.remove('hidden'); else th.classList.add('hidden');
                newHead.appendChild(th);
            }
        });
        origThs.forEach(th => {
            const k = th.dataset.colKey ? th.dataset.colKey : slug(th.textContent || '');
            if (!sorted.find(s => s.key === k)) newHead.appendChild(th);
        });
        thead.innerHTML = '';
        thead.appendChild(newHead);

        const rows = qsa(tbody, 'tr');
        rows.forEach(row => {
            const cells = Array.from(row.children);
            const newRow = document.createElement('tr');
            sorted.forEach(col => {
                const origIndex = origThs.findIndex(t => {
                    const k = t.dataset.colKey ? t.dataset.colKey : slug(t.textContent || '');
                    return k === col.key;
                });
                if (origIndex >= 0 && cells[origIndex]) newRow.appendChild(cells[origIndex]); else newRow.appendChild(document.createElement('td'));
            });
            cells.forEach((c, idx) => {
                const k = origThs[idx] ? (origThs[idx].dataset.colKey ? origThs[idx].dataset.colKey : slug(origThs[idx].textContent || '')) : null;
                if (!sorted.find(s => s.key === k)) newRow.appendChild(c);
            });
            row.parentNode.replaceChild(newRow, row);
        });
    }

    async function loadSettings(key) {
        try {
            return await fetchJson(API_URL + '?key=' + encodeURIComponent(key), {
                method: 'GET',
                credentials: 'same-origin'
            });
        } catch (e) {
            console.warn('loadSettings', e);
            return {};
        }
    }

    async function saveSettings(key, settings) {
        try {
            return await fetchJson(API_URL, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.getCsrf()},
                body: JSON.stringify({key, settings})
            });
        } catch (e) {
            console.error('saveSettings', e);
            throw e;
        }
    }

    function renderSettingsForm(columns) {
        const form = qs(document, '#settings-form');
        if (!form) return;
        form.innerHTML = '';
        const list = document.createElement('div');
        list.className = 'settings-list';
        columns.forEach((col, idx) => {
            const row = document.createElement('div');
            row.className = 'settings-item';
            row.draggable = true;
            row.dataset.colKey = col.key;
            row.innerHTML = `<span class="drag-handle">☰</span><div class="col-wrap"><input type="checkbox" ${col.visible ? 'checked' : ''} data-col-key="${col.key}"><span class="col-title">${col.title || col.key}</span></div>`;
            row.addEventListener('dragstart', e => {
                e.dataTransfer.setData('text/plain', col.key);
                row.classList.add('dragging');
            });
            row.addEventListener('dragend', () => row.classList.remove('dragging'));
            row.addEventListener('dragover', e => {
                e.preventDefault();
                const d = list.querySelector('.dragging');
                if (!d || d === row) return;
                const rect = row.getBoundingClientRect();
                const after = (e.clientY - rect.top) > rect.height / 2;
                if (after) row.parentNode.insertBefore(d, row.nextSibling); else row.parentNode.insertBefore(d, row);
            });
            list.appendChild(row);
        });
        form.appendChild(list);
    }

    async function initTable({tableKey, wrapper}) {
        if (!tableKey || !wrapper) return;
        const domCols = readColumnsFromDOM(wrapper);
        const saved = await loadSettings(tableKey);
        const effective = (saved && saved.settings && saved.settings.columns) ? saved.settings : {columns: domCols};
        applySettingsToDOM(wrapper, effective);

        const btn = wrapper.querySelector('[data-settings-btn]') || wrapper.querySelector('.settings-button') || wrapper.querySelector('#settings-btn');
        if (!btn) return;
        btn.addEventListener('click', async () => {
            const cols = readColumnsFromDOM(wrapper);
            const toRender = (saved && saved.settings && saved.settings.columns) ? saved.settings.columns : cols;
            renderSettingsForm(toRender);
            openModal();

            const saveBtn = qs(document, '#settings-save'), cancelBtn = qs(document, '#settings-cancel');
            if (cancelBtn) cancelBtn.onclick = closeModal;
            if (saveBtn) {
                saveBtn.onclick = async (ev) => {
                    ev.preventDefault();
                    const items = qsa(document, '.settings-item');
                    const newCols = items.map((it, idx) => {
                        const key = it.dataset.colKey;
                        const cb = it.querySelector('input[type="checkbox"]');
                        const titleEl = it.querySelector('.col-title');
                        return {
                            key,
                            title: titleEl ? titleEl.textContent.trim() : key,
                            visible: !!(cb && cb.checked),
                            order: idx
                        };
                    });
                    const newSettings = {columns: newCols};
                    await saveSettings(tableKey, newSettings);
                    applySettingsToDOM(wrapper, newSettings);
                    closeModal();
                };
            }
        });
    }

    function autoInit() {
        const wrappers = qsa(document, '.table-wrapper[data-table-key]');
        wrappers.forEach(w => {
            const key = w.dataset.tableKey;
            initTable({tableKey: key, wrapper: w}).catch(e => console.error('initTable', e));
        });
    }

    window.TableSettings = {initTable, autoInit, loadSettings, saveSettings};

    document.addEventListener('DOMContentLoaded', () => {
        autoInit();
        const overlay = qs(document, '#modal-overlay');
        if (overlay) overlay.addEventListener('click', () => {
            const m = qs(document, '#settings-modal');
            if (m) m.classList.remove('show');
            overlay.classList.remove('show');
        });
    });
})();
