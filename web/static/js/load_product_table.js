// load_product_table.js — финальная версия: модалка + автокомплит для related fields
(function () {
    const API_BASE = "/api/";
    const PRODUCTS_API = API_BASE + "products/";
    const GET_TABLE_SETTINGS = "/api/get_table_settings/?table=products";
    const ADD_IMAGE_ENDPOINT = (id) => `/products/${id}/add-image/`;
    let currentProducts = [];
    let currentUploadProductId = null;

    const defaultColumns = [
        {field: "product_code", label: "Код товара", visible: true},
        {field: "client", label: "Клиент", visible: true},
        {field: "cargo_status", label: "Статус", visible: true},
        {field: "warehouse", label: "Склад", visible: false},
        {field: "weight", label: "Вес", visible: false},
        {field: "cost", label: "Стоимость", visible: false},
        {field: "images", label: "Изображения", visible: true},
    ];

    function el(q) {
        return document.querySelector(q);
    }

    function els(q) {
        return Array.from(document.querySelectorAll(q));
    }

    async function fetchJSON(url, opts = {}) {
        const fetchOpts = Object.assign({credentials: "same-origin"}, opts);
        const res = await fetch(url, fetchOpts);
        if (!res.ok) {
            const txt = await res.text().catch(() => "");
            const err = new Error(`HTTP ${res.status}: ${url}`);
            err.status = res.status;
            err.body = txt;
            throw err;
        }
        try {
            return await res.json();
        } catch (e) {
            return {__raw_text: await res.text().catch(() => "")};
        }
    }

    // ---------------- Autocomplete helpers ----------------
    const RELATED_API_MAP = {
        client: "/api/clients/",
        cargo_status: "/api/cargo_statuses/",
        warehouse: "/api/warehouses/",
        // add more if needed
    };

    function buildSearchUrlForField(field, q) {
        const base = (window.RELATED_API_MAP && window.RELATED_API_MAP[field])
            ? window.RELATED_API_MAP[field]
            : (RELATED_API_MAP[field] || (`${API_BASE}${field}s/`));
        const sep = base.includes("?") ? "&" : "?";
        return `${base}${sep}search=${encodeURIComponent(q)}&page_size=7`;
    }

    function debounce(fn, wait = 220) {
        let t;
        return (...args) => {
            clearTimeout(t);
            t = setTimeout(() => fn(...args), wait);
        };
    }

    function closeDropdown(dd) {
        if (!dd) return;
        dd.remove();
    }

    function makeDropdown(items) {
        const dd = document.createElement("div");
        dd.className = "autocomplete-dropdown";
        items.forEach((it, idx) => {
            const row = document.createElement("div");
            row.className = "autocomplete-row";
            row.tabIndex = 0;
            row.dataset._idx = idx;
            row.textContent = (it && (it.name || it.client_code || it.title || it.code || it.id)) || String(it || "");
            row._remote = it;
            dd.appendChild(row);
        });
        return dd;
    }

    function attachAutocomplete(inputEl, hiddenEl, field) {
        const container = inputEl.parentElement;
        if (getComputedStyle(container).position === 'static') container.style.position = 'relative';

        let dropdown = null;
        let focusedIndex = -1;

        function renderDropdown(items) {
            closeDropdown(dropdown);
            if (!items || items.length === 0) return;
            dropdown = makeDropdown(items.slice(0, 7));

            // position relative to inputEl (left/top) — minimal inline positioning
            const left = inputEl.offsetLeft;
            const top = inputEl.offsetTop + inputEl.offsetHeight + 6;
            dropdown.style.left = `${left}px`;
            dropdown.style.top = `${top}px`;
            dropdown.style.minWidth = `${Math.max(inputEl.offsetWidth, 260)}px`;

            container.appendChild(dropdown);
            focusedIndex = -1;

            dropdown.addEventListener("mousedown", (ev) => ev.preventDefault());

            dropdown.addEventListener("click", (ev) => {
                const row = ev.target.closest(".autocomplete-row");
                if (!row) return;
                const it = row._remote;
                applySelection(it);
                closeDropdown(dropdown);
            });
        }

        function applySelection(it) {
            const display = (it && (it.name || it.client_code || it.title || it.code || it.id)) || String(it || "");
            inputEl.value = display;
            if (hiddenEl) {
                const idv = (it && (it.id || it.pk)) ? (it.id || it.pk) : "";
                hiddenEl.value = idv;
            }
            inputEl.focus();
            inputEl.setSelectionRange(inputEl.value.length, inputEl.value.length);
        }

        function onKeyDown(ev) {
            if (!dropdown) return;
            const rows = Array.from(dropdown.querySelectorAll(".autocomplete-row"));
            if (ev.key === "ArrowDown") {
                ev.preventDefault();
                focusedIndex = Math.min(rows.length - 1, focusedIndex + 1);
                rows.forEach((r, i) => r.classList.toggle('active', i === focusedIndex));
                rows[focusedIndex] && rows[focusedIndex].focus();
            } else if (ev.key === "ArrowUp") {
                ev.preventDefault();
                focusedIndex = Math.max(0, focusedIndex - 1);
                rows.forEach((r, i) => r.classList.toggle('active', i === focusedIndex));
                rows[focusedIndex] && rows[focusedIndex].focus();
            } else if (ev.key === "Enter") {
                ev.preventDefault();
                if (focusedIndex >= 0 && rows[focusedIndex]) {
                    const it = rows[focusedIndex]._remote;
                    applySelection(it);
                    closeDropdown(dropdown);
                }
            } else if (ev.key === "Escape") {
                closeDropdown(dropdown);
            }
        }

        const doSearch = debounce(async (q) => {
            if (!q || q.length < 1) {
                closeDropdown(dropdown);
                return;
            }
            try {
                const url = buildSearchUrlForField(field, q);
                const data = await fetchJSON(url).catch(() => null);
                let items = [];
                if (!data) items = [];
                else if (Array.isArray(data.results)) items = data.results;
                else if (Array.isArray(data)) items = data;
                else if (data && data.results) items = data.results;
                const qlow = q.toLowerCase();
                items = items.filter(it => {
                    const s = (it && (it.name || it.client_code || it.title || it.code || it.id || "")).toString().toLowerCase();
                    return s.includes(qlow);
                }).slice(0, 7);
                renderDropdown(items);
            } catch (e) {
                console.error("autocomplete fetch error", e);
            }
        }, 220);

        inputEl.addEventListener("input", () => {
            if (hiddenEl) hiddenEl.value = "";
            const q = inputEl.value.trim();
            if (!q) {
                closeDropdown(dropdown);
                return;
            }
            doSearch(q);
        });

        inputEl.addEventListener("keydown", onKeyDown);
        inputEl.addEventListener("blur", () => setTimeout(() => closeDropdown(dropdown), 180));
    }

    // ---------------- Table & rendering ----------------
    async function loadTableSettings() {
        try {
            const cfg = await fetchJSON(GET_TABLE_SETTINGS);
            if (cfg && Array.isArray(cfg.columns)) {
                const saved = {};
                cfg.columns.forEach(c => {
                    if (c.field) saved[c.field] = c;
                });
                const merged = defaultColumns.map(d => {
                    if (saved[d.field]) return Object.assign({}, d, {
                        visible: !!saved[d.field].visible,
                        label: saved[d.field].label || d.label
                    });
                    return d;
                });
                Object.keys(saved).forEach(f => {
                    if (!merged.some(m => m.field === f)) merged.push(saved[f]);
                });
                return merged;
            }
        } catch (e) {
            console.warn("[product_table] loadTableSettings failed, using defaults", e);
        }
        return defaultColumns;
    }

    async function loadProducts() {
        const url = PRODUCTS_API + "?page_size=1000";
        const data = await fetchJSON(url);
        if (data && Array.isArray(data.results)) return data.results;
        if (Array.isArray(data)) return data;
        if (data && data.results) return data.results;
        return [];
    }

    function formatCell(value) {
        if (value === null || value === undefined) return "";
        return String(value);
    }

    function renderTable(columns, products) {
        const table = el("#product-table");
        if (!table) {
            console.error("[product_table] product table element not found");
            return;
        }
        const thead = table.querySelector("thead");
        const tbody = table.querySelector("tbody");
        thead.innerHTML = "";
        tbody.innerHTML = "";

        const visibleCols = columns.filter(c => c.visible);

        const trh = document.createElement("tr");
        visibleCols.forEach(col => {
            const th = document.createElement("th");
            th.textContent = col.label || col.field;
            th.setAttribute("data-field", col.field);
            const hint = document.createElement("span");
            hint.className = "sortable-hint";
            hint.textContent = " ⌄";
            th.appendChild(hint);
            trh.appendChild(th);
        });
        thead.appendChild(trh);

        if (!products || products.length === 0) {
            if (el("#product-table-empty")) el("#product-table-empty").style.display = "";
            table.style.display = "none";
            if (el("#loader")) el("#loader").style.display = "none";
            return;
        } else {
            if (el("#product-table-empty")) el("#product-table-empty").style.display = "none";
            table.style.display = "";
        }

        products.forEach(p => {
            const tr = document.createElement("tr");
            visibleCols.forEach(col => {
                const td = document.createElement("td");
                let val = "";
                switch (col.field) {
                    case "client":
                        val = p.client_code || p.client_id || (p.client && (p.client.client_code || p.client.name)) || "";
                        break;
                    case "cargo_status":
                        val = p.cargo_status_name || p.cargo_status_id || (p.cargo_status && (p.cargo_status.name || p.cargo_status)) || "";
                        break;
                    case "images":
                        val = (p.images && Array.isArray(p.images) && p.images.length) ? `${p.images.length} шт.` : "";
                        break;
                    default:
                        val = p[col.field] !== undefined ? p[col.field] : "";
                }
                td.textContent = formatCell(val);
                tr.appendChild(td);
            });

            if (p && (p.id || p.pk)) tr.dataset.id = p.id || p.pk;
            tr.setAttribute("tabindex", "0");

            tr.addEventListener("click", () => {
                openProductModal({__mode: "edit", __model: "products", __id: (p.id || p.pk), __product: p});
            });

            tr.addEventListener("keydown", (ev) => {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    tr.click();
                }
            });

            tbody.appendChild(tr);
        });

        if (el("#loader")) el("#loader").style.display = "none";
    }

    // ---- image upload (unchanged) ----
    function openImageModal(productId) {
        currentUploadProductId = productId;
        const status = el("#image-upload-status");
        if (status) status.textContent = "";
        const input = el("#image-file-input");
        if (input) input.value = "";
        const modal = el("#image-upload-modal");
        if (modal) modal.style.display = "block";
    }

    function closeImageModal() {
        const modal = el("#image-upload-modal");
        if (modal) modal.style.display = "none";
        currentUploadProductId = null;
    }

    async function sendImage() {
        const input = el("#image-file-input");
        const status = el("#image-upload-status");
        if (!input || !input.files || input.files.length === 0) {
            if (status) status.textContent = "Выберите файл.";
            return;
        }
        if (!currentUploadProductId) {
            if (status) status.textContent = "Нет product id.";
            return;
        }
        const fd = new FormData();
        fd.append("image_file", input.files[0]);
        try {
            const res = await fetch(ADD_IMAGE_ENDPOINT(currentUploadProductId), {
                method: "POST",
                credentials: "same-origin",
                body: fd
            });
            if (!res.ok) {
                const txt = await res.text();
                if (status) status.textContent = `Ошибка: ${res.status}`;
                console.error("image upload error", res.status, txt);
                return;
            }
            const json = await res.json();
            if (status) status.textContent = json.message || "OK";
            await main();
            closeImageModal();
        } catch (e) {
            console.error("sendImage error", e);
            if (status) status.textContent = "Ошибка загрузки";
        }
    }

    function getCsrf() {
        const name = 'csrftoken=';
        const cookies = document.cookie.split(';').map(s => s.trim());
        for (const c of cookies) if (c.startsWith(name)) return c.substring(name.length);
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    // ---------------- Modal: create / edit product ----------------
    async function openProductModal(context = {}) {
        const product = context.__product || {};
        const mode = context.__mode || 'edit';
        const id = context.__id || (product.id || product.pk) || null;

        // Определяем поле с кодом товара (первое попавшееся)
        const codeCandidates = ['product', 'code', 'product_code', 'sku', 'code_product'];
        let codeFieldName = null;
        let codeValue = null;
        for (const c of codeCandidates) {
            if (product[c] !== undefined && product[c] !== null && String(product[c]).trim() !== '') {
                codeFieldName = c;
                codeValue = String(product[c]);
                break;
            }
        }

        // --- Строим DOM модалки (не апендим overlay вручную) ---
        const form = document.createElement('form');
        form.className = 'modal-form';

        const modalRoot = document.createElement('div');
        modalRoot.className = 'modal';

        // header: показываем "Товар: <код>" в режиме редактирования
        const header = document.createElement('div');
        header.className = 'modal-header';
        const titleSpan = document.createElement('span');
        titleSpan.textContent = (mode === 'create') ? 'Добавить товар' : `Редактировать товар ${id ? '#' + id : ''}`;
        header.appendChild(titleSpan);
        if (mode === 'edit' && codeValue) {
            const codeSpan = document.createElement('span');
            codeSpan.style.fontWeight = '500';
            codeSpan.style.color = '#1f2937';
            codeSpan.textContent = `Товар: ${codeValue}`;
            header.appendChild(codeSpan);
        }
        modalRoot.appendChild(header);

        // body
        const body = document.createElement('div');
        body.className = 'modal-body';
        modalRoot.appendChild(body);

        const fieldsContainer = document.createElement('div');
        fieldsContainer.className = 'modal-fields';
        body.appendChild(fieldsContainer);

        // вычисляем поля
        const defaultFields = (typeof defaultColumns !== 'undefined' && Array.isArray(defaultColumns)) ? defaultColumns.map(c => c.field) : [];
        const productKeys = Object.keys(product || {});
        const rawFields = Array.from(new Set([...(Array.isArray(defaultFields) ? defaultFields : []), ...productKeys]));
        const fields = rawFields.map(f => String(f).replace(/(_id|_name|_code|_pk)$/, ''));

        const relatedFields = new Set();
        for (const f of fields) {
            const base = String(f);
            if (
                (product[base] && typeof product[base] === 'object' && product[base] !== null) ||
                product[`${base}_id`] !== undefined ||
                product[`${base}_name`] !== undefined ||
                product[`${base}_code`] !== undefined ||
                product[`${base}_pk`] !== undefined
            ) relatedFields.add(base);
        }

        // Рендерим поля — пропускаем поле с кодом товара в режиме редактирования
        for (const f of fields) {
            const base = String(f);
            if (mode === 'edit' && codeFieldName && base === codeFieldName) continue; // убираем поле кода из тела

            const raw = (product[base] !== undefined && product[base] !== null) ? product[base] :
                (product[`${base}_name`] !== undefined && product[`${base}_name`] !== null) ? product[`${base}_name`] :
                    (product[`${base}_code`] !== undefined && product[`${base}_code`] !== null) ? product[`${base}_code`] : '';

            let displayValue = '';
            if (raw && typeof raw === 'object') displayValue = raw.name || raw.client_code || raw.title || raw.code || raw.id || '';
            else displayValue = raw !== undefined && raw !== null ? String(raw) : '';

            const fieldWrapper = document.createElement('div');
            fieldWrapper.className = 'modal-row';

            const labelEl = document.createElement('label');
            labelEl.textContent = base.replace(/_/g, ' ').replace(/\b\w/g, ch => ch.toUpperCase());
            fieldWrapper.appendChild(labelEl);

            const inputEl = document.createElement('input');
            inputEl.type = 'text';
            inputEl.name = base;
            inputEl.value = displayValue;
            inputEl.className = 'modal-input';
            fieldWrapper.appendChild(inputEl);

            if (relatedFields.has(base)) {
                const hid = document.createElement('input');
                hid.type = 'hidden';
                hid.name = `${base}_id`;
                hid.value = (product[`${base}_id`] !== undefined && product[`${base}_id`] !== null)
                    ? product[`${base}_id`]
                    : ((product[base] && (product[base].id || product[base].pk)) ? (product[base].id || product[base].pk) : '');
                fieldWrapper.appendChild(hid);
            }

            fieldsContainer.appendChild(fieldWrapper);
        }

        // footer
        const footer = document.createElement('div');
        footer.className = 'modal-footer';
        const btnCancel = document.createElement('button');
        btnCancel.type = 'button';
        btnCancel.className = 'btn-cancel';
        btnCancel.textContent = 'Отмена';
        const btnSave = document.createElement('button');
        btnSave.type = 'submit';
        btnSave.className = 'btn-save';
        btnSave.textContent = 'Сохранить';
        footer.appendChild(btnCancel);
        footer.appendChild(btnSave);

        form.appendChild(modalRoot);
        form.appendChild(footer);

        // открываем через универсальную
        const inst = openModal({html: form, modalName: 'product', closable: true});
        if (!inst) return null;

        const modal = inst.modal;
        const realForm = modal.tagName === 'FORM' ? modal : modal.querySelector('form') || modal;
        const realFieldsContainer = realForm.querySelector('.modal-fields');

        // инициализация автокомплита (после вставки в DOM)
        for (const f of fields) {
            if (!relatedFields.has(f)) continue;
            const visible = realForm.querySelector(`input[name="${f}"]`);
            const hidden = realForm.querySelector(`input[name="${f}_id"]`);
            try {
                if (typeof attachAutocomplete === 'function') attachAutocomplete(visible, hidden, f);
            } catch (e) {
                console.warn('attachAutocomplete failed for', f, e);
            }
        }

        setTimeout(() => {
            const first = realForm.querySelector('input, textarea, select');
            if (first) first.focus();
        }, 0);

        // обработчики
        function cleanup() {
            try {
                realForm.removeEventListener('submit', onSubmit);
                btnCancel.removeEventListener('click', onCancel);
            } catch (e) {
            }
        }

        function onCancel(ev) {
            ev && ev.preventDefault();
            inst.close();
        }

        async function onSubmit(ev) {
            ev.preventDefault();
            const fd = new FormData(realForm);
            const entries = Array.from(fd.entries());
            const map = {};
            for (const [k, v] of entries) map[k] = v;

            const payload = {};
            for (const f of fields) {
                if (relatedFields.has(f)) {
                    const hidName = `${f}_id`;
                    const hidVal = map[hidName];
                    if (hidVal) {
                        payload[f] = Number(hidVal);
                        continue;
                    }
                    payload[f] = map[f] || null;
                } else {
                    if (map[f] !== undefined) payload[f] = map[f];
                }
            }
            Object.keys(payload).forEach(k => {
                if (payload[k] === '' || payload[k] === null) delete payload[k];
            });

            try {
                const csrftoken = typeof getCsrf === 'function' ? getCsrf() : '';
                let res;
                if (mode === 'create') {
                    res = await fetch(PRODUCTS_API, {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrftoken},
                        body: JSON.stringify(payload)
                    });
                } else {
                    if (!id) throw new Error('Нет id продукта');
                    res = await fetch(PRODUCTS_API + id + '/', {
                        method: 'PUT',
                        credentials: 'same-origin',
                        headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrftoken},
                        body: JSON.stringify(payload)
                    });
                }
                if (!res.ok) {
                    const txt = await res.text().catch(() => null);
                    console.error('product save error', res.status, txt);
                    alert('Ошибка сохранения. Смотрите консоль.');
                    return;
                }
                inst.close();
                cleanup();
                if (typeof main === 'function') await main();
                else if (typeof window.reloadProductsTable === 'function') window.reloadProductsTable();
            } catch (err) {
                console.error('save product error', err);
                alert('Ошибка сохранения. Смотрите консоль.');
            }
        }

        btnCancel.addEventListener('click', onCancel);
        realForm.addEventListener('submit', onSubmit);

        return inst;
    }


    // bind add-product btn
    const btnAddProduct = el('#btn-add-product');
    if (btnAddProduct) btnAddProduct.addEventListener('click', () => openProductModal({__mode: 'create'}));

    async function main() {
        try {
            if (el("#loader")) el("#loader").style.display = "";
            const cols = await loadTableSettings();
            const prods = await loadProducts();
            currentProducts = prods;
            renderTable(cols, prods);
        } catch (e) {
            console.error("[product_table] Ошибка инициализации:", e);
            if (el("#loader")) el("#loader").style.display = "none";
            if (el("#product-table-empty")) el("#product-table-empty").style.display = "";
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        const sendBtn = el("#image-upload-send");
        if (sendBtn) sendBtn.addEventListener("click", sendImage);
        const cancelBtn = el("#image-upload-cancel");
        if (cancelBtn) cancelBtn.addEventListener("click", closeImageModal);

        const btnSettings = el("#btn-table-settings");
        if (btnSettings) btnSettings.addEventListener("click", () => {
            window.open("/settings_modal", "_blank");
        });

        const btnAdd = el("#btn-add-product");
        if (btnAdd) btnAdd.addEventListener("click", () => openProductModal({__mode: 'create'}));

        main();
    });

})();
