// ===============================
//   Модалки товаров (новая версия)
//   Полная поддержка modal.css
//   Полное автодополнение клиента (как в home.js)
// ===============================
function getCSRF() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}
// ===============================
//   ADD PRODUCT MODAL
// ===============================
function openProductAdd() {

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";

    overlay.innerHTML = `
        <div class="modal">

            <div class="modal-header">
                <span>Приём товара на склад</span>
            </div>

            <div class="modal-body modal-fields">

                <!-- CLIENT -->
                <div class="modal-row select-search-wrapper">
                    <label>Код клиента *</label>
                    <input id="add_client_code" 
                           class="select-search-input modal-input"
                           autocomplete="off"
                           placeholder="Введите код клиента...">
                </div>

                <!-- WAREHOUSE -->
                <div class="modal-row">
                    <label>Склад *</label>
                    <select id="add_warehouse" class="modal-input"></select>
                </div>

                <!-- CARGO TYPE -->
                <div class="modal-row">
                    <label>Тип груза *</label>
                    <select id="add_cargo_type" class="modal-input"></select>
                </div>

                <!-- CARGO STATUS -->
                <div class="modal-row">
                    <label>Статус груза *</label>
                    <select id="add_cargo_status" class="modal-input"></select>
                </div>

                <!-- PACKAGING -->
                <div class="modal-row">
                    <label>Тип упаковки *</label>
                    <select id="add_packaging" class="modal-input"></select>
                </div>

                <!-- PHOTO -->
                <div class="modal-row">
                    <label>Фото</label>
                    <div style="flex:1;">
                        <button id="btnAddPhoto" class="btn-secondary">Добавить фото</button>
                    </div>
                </div>

            </div>

            <div class="modal-footer">
                <button class="btn-secondary" id="add_close">Отмена</button>
                <button class="btn-primary" id="add_save">Создать</button>
            </div>

        </div>
    `;

    document.body.appendChild(overlay);

    // закрытие
    document.getElementById("add_close").onclick = () => {
        if (dropdown) dropdown.remove();
        overlay.remove();
    };

    // ===============================
    //  LOAD REFERENCES (SELECTS)
    // ===============================
    async function loadRef(url, selectEl) {
        const r = await fetch(url);
        const j = await r.json();
        (j.results || j).forEach(row => {
            const o = document.createElement("option");
            o.value = row.id;
            o.textContent = row.name;
            selectEl.appendChild(o);
        });
    }

    const selWarehouse = document.getElementById("add_warehouse");
    const selCargoType = document.getElementById("add_cargo_type");
    const selCargoStatus = document.getElementById("add_cargo_status");
    const selPackaging = document.getElementById("add_packaging");

    const refPromises = [
        loadRef("/api/warehouses/?page_size=9999", selWarehouse),
        loadRef("/api/cargo-types/?page_size=9999", selCargoType),
        loadRef("/api/cargo-statuses/?page_size=9999", selCargoStatus),
        loadRef("/api/packaging-types/?page_size=9999", selPackaging),
    ];

    async function applyUserDefaults() {
        try {
            const r = await fetch("/api/user/cargo-defaults/", { credentials: "include" });
            if (!r.ok) return;
            const d = await r.json();

            if (d.warehouse && d.warehouse.id) selWarehouse.value = String(d.warehouse.id);
            if (d.cargo_type && d.cargo_type.id) selCargoType.value = String(d.cargo_type.id);
            if (d.cargo_status && d.cargo_status.id) selCargoStatus.value = String(d.cargo_status.id);
            if (d.packaging_type && d.packaging_type.id) selPackaging.value = String(d.packaging_type.id);
        } catch (e) {
            // молча, чтобы не ломать UX
        }
    }

    Promise.all(refPromises).then(applyUserDefaults);

    // ===============================
    //  AUTOCOMPLETE CLIENT (как было)
    // ===============================
    const input = overlay.querySelector("#add_client_code");

    let dropdown = document.createElement("div");
    dropdown.className = "client-autocomplete autocomplete-list hidden";
    overlay.appendChild(dropdown);

    let clientsCache = [];

    async function loadClients() {
        if (clientsCache.length) return clientsCache;
        const r = await fetch("/api/get_clients/?page_size=99999");
        const j = await r.json();
        clientsCache = j.results || j;
        return clientsCache;
    }

    async function showDropdown() {
        const q = input.value.trim().toLowerCase();
        const list = await loadClients();

        const filtered = q
            ? list.filter(c => c.client_code.toLowerCase().includes(q))
            : list.slice(0, 7);

        dropdown.innerHTML = filtered.length
            ? filtered.map(c => `<div class="autocomplete-item">${c.client_code}</div>`).join("")
            : `<div class="autocomplete-empty">Нет совпадений</div>`;

        dropdown.style.position = "absolute";
        const rect = input.getBoundingClientRect();
        dropdown.style.top = (rect.top + rect.height) + "px";
        dropdown.style.left = rect.left + "px";
        dropdown.style.width = rect.width + "px";
        dropdown.classList.remove("hidden");

        dropdown.querySelectorAll(".autocomplete-item").forEach(item => {
            item.addEventListener("mousedown", (e) => {
                e.stopPropagation();
                input.value = item.textContent.trim();
                dropdown.classList.add("hidden");
                setTimeout(() => dropdown.innerHTML = "", 50);
            });
        });
    }

    input.addEventListener("input", showDropdown);
    input.addEventListener("focus", showDropdown);

    document.addEventListener("mousedown", (e) => {
        if (e.target.closest(".autocomplete-item")) return;
        if (!dropdown.contains(e.target) && e.target !== input) {
            dropdown.classList.add("hidden");
        }
    });

    // ===============================
    //  SAVE
    // ===============================
    document.getElementById("add_save").onclick = async () => {

        const clientCode = input.value.trim();
        if (!clientCode) return;

        // ищем клиента
        const r1 = await fetch(`/api/get_clients/?search=${clientCode}`);
        const js1 = await r1.json();
        const client = js1.results.find(c => c.client_code === clientCode);
        if (!client) return;

        // генерируем код нового товара
        const r2 = await fetch("/api/generate/product/", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRF(),
            },
            body: JSON.stringify({ client_id: client.id })
        });
        const js2 = await r2.json();

        // отправляем CREATE
        await fetch("/api/products-table/", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRF()
            },
            body: JSON.stringify({
                client_id: client.id,
                product_code: js2.product_code,

                warehouse_id: selWarehouse.value,
                cargo_type_id: selCargoType.value,
                cargo_status_id: selCargoStatus.value,
                packaging_type_id: selPackaging.value,
            })
        });

        overlay.remove();
        PT_reset();
        PT_load();
    };

}


async function loadFullProductAndEdit(productId) {

    const r = await fetch(`/api/products-table/${productId}/`, {
        credentials: "include"
    });
    const full = await r.json();

    openProductEdit(full);
}


//   EDIT PRODUCT MODAL
function openProductEdit(product) {

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";

    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <span>Товар: ${product.product_code}</span>
            </div>

            <div class="modal-body">

                <div class="modal-row">
                    <button id="btnEditProduct" class="btn-primary" style="width:100%;">
                        ✏ Редактировать товар
                    </button>
                </div>

                <div class="modal-row">
                    <button id="btnCalcFinance" class="btn-secondary" style="width:100%;">
                        💰 Рассчитать финансы
                    </button>
                </div>

            </div>

            <div class="modal-footer">
                <button class="btn-secondary" id="edit_close">Закрыть</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    // закрытие
    document.getElementById("edit_close").onclick = () => overlay.remove();

    // обработчики кнопок
    document.getElementById("btnEditProduct").onclick = () => {
        overlay.remove();
        stubEditProduct(product);
    };

    document.getElementById("btnCalcFinance").onclick = () => {
        overlay.remove();
        stubCalcFinance(product);
    };
}

function stubEditProduct(product) {

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";

    overlay.innerHTML = `
        <div class="modal">

            <div class="modal-header">
                <span>Редактирование товара</span>
            </div>

            <div class="modal-body modal-fields">

                <!-- INFO -->
                <div class="modal-row">
                    <label>Код товара</label>
                    <div class="modal-info">${product.product_code}</div>
                </div>

                <div class="modal-row">
                    <label>Клиент</label>
                    <div class="modal-info">${product.client}</div>
                </div>

                <div class="modal-row">
                    <label>Дата записи</label>
                    <div class="modal-info">${product.record_date || ""}</div>
                </div>

                <!-- REFERENCES (справочники) -->
                <div class="modal-row">
                    <label>Склад *</label>
                    <select id="edit_warehouse" class="modal-input"></select>
                </div>

                <div class="modal-row">
                    <label>Тип груза *</label>
                    <select id="edit_cargo_type" class="modal-input"></select>
                </div>

                <div class="modal-row">
                    <label>Статус груза *</label>
                    <select id="edit_cargo_status" class="modal-input"></select>
                </div>

                <div class="modal-row">
                    <label>Тип упаковки *</label>
                    <select id="edit_packaging" class="modal-input"></select>
                </div>

                <!-- EDITABLE -->
                <div class="modal-row">
                    <label>Описание</label>
                    <input id="edit_description" class="modal-input" value="${product.cargo_description || ""}">
                </div>

                <div class="modal-row select-search-wrapper">
                    <label>Пункт отправления (склад)</label>
                    <input id="edit_departure"
                           class="select-search-input modal-input"
                           autocomplete="off"
                           placeholder="Начните ввод..."
                           value="${product.departure_place || ""}">
                </div>

                <div class="modal-row select-search-wrapper">
                    <label>Пункт назначения (склад)</label>
                    <input id="edit_destination"
                           class="select-search-input modal-input"
                           autocomplete="off"
                           placeholder="Начните ввод..."
                           value="${product.destination_place || ""}">
                </div>

                <div class="modal-row">
                    <label>Вес</label>
                    <input id="edit_weight" class="modal-input" type="number" step="0.01" value="${product.weight || ""}">
                </div>

                <div class="modal-row">
                    <label>Объём</label>
                    <input id="edit_volume" class="modal-input" type="number" step="0.01" value="${product.volume || ""}">
                </div>

                <div class="modal-row">
                    <label>Стоимость товара</label>
                    <input id="edit_cost" class="modal-input" type="number" step="0.01" value="${product.cost || ""}">
                </div>

                <div class="modal-row">
                    <label>Срок доставки</label>
                    <input id="edit_delivery_time" class="modal-input" type="number" step="0.1" value="${product.delivery_time || ""}">
                </div>

                <div class="modal-row">
                    <label>Дата отправки</label>
                    <input id="edit_shipping_date" class="modal-input" type="date" value="${product.shipping_date || ""}">
                </div>

                <div class="modal-row">
                    <label>Дата доставки</label>
                    <input id="edit_delivery_date" class="modal-input" type="date" value="${product.delivery_date || ""}">
                </div>

                <div class="modal-row">
                    <label>Комментарий</label>
                    <textarea id="edit_comment" class="modal-input" style="height:70px;">${product.comment || ""}</textarea>
                </div>

            </div>

            <div class="modal-footer">
                <button class="btn-secondary" id="edit_cancel">Отмена</button>
                <button class="btn-primary" id="edit_save">Сохранить</button>
            </div>

        </div>
    `;

    document.body.appendChild(overlay);

    // ----------------------------
    // helpers: load refs
    // ----------------------------
    async function loadRef(url, selectEl, selectedId) {
        const r = await fetch(url, { credentials: "include" });
        const j = await r.json();
        const rows = j.results || j;

        selectEl.innerHTML = "";

        // пустой вариант (на всякий)
        const emptyOpt = document.createElement("option");
        emptyOpt.value = "";
        emptyOpt.textContent = "—";
        selectEl.appendChild(emptyOpt);

        rows.forEach(row => {
            const o = document.createElement("option");
            o.value = row.id;
            o.textContent = row.name;
            selectEl.appendChild(o);
        });

        if (selectedId !== null && selectedId !== undefined) {
            selectEl.value = String(selectedId);
        }
    }

    // грузим справочники и выставляем текущие значения товара
    loadRef("/api/warehouses/?page_size=9999", document.getElementById("edit_warehouse"), product.warehouse_id);
    loadRef("/api/cargo-types/?page_size=9999", document.getElementById("edit_cargo_type"), product.cargo_type_id);
    loadRef("/api/cargo-statuses/?page_size=9999", document.getElementById("edit_cargo_status"), product.cargo_status_id);
    loadRef("/api/packaging-types/?page_size=9999", document.getElementById("edit_packaging"), product.packaging_type_id);

    // ----------------------------
    // Warehouses autocomplete (до 7 строк + скролл)
    // ----------------------------
    let warehousesCache = [];
    async function loadWarehouses() {
        if (warehousesCache.length) return warehousesCache;
        const r = await fetch("/api/warehouses/?page_size=9999", { credentials: "include" });
        const j = await r.json();
        warehousesCache = j.results || j;
        return warehousesCache;
    }

    function bindWarehouseAutocomplete(inputEl) {
        const dropdown = document.createElement("div");
        dropdown.className = "autocomplete-list hidden";
        dropdown.style.position = "absolute";
        dropdown.style.maxHeight = "224px";  // ~7 строк
        dropdown.style.overflowY = "auto";
        dropdown.style.zIndex = "10000";
        overlay.appendChild(dropdown);

        async function show() {
            const list = await loadWarehouses();
            const q = inputEl.value.trim().toLowerCase();

            const filtered = q
                ? list.filter(w => (w.name || "").toLowerCase().includes(q))
                : list;

            dropdown.innerHTML = filtered.length
                ? filtered.map(w => `<div class="autocomplete-item">${w.name}</div>`).join("")
                : `<div class="autocomplete-empty">Нет совпадений</div>`;

            const rect = inputEl.getBoundingClientRect();
            dropdown.style.top = (rect.top + rect.height) + "px";
            dropdown.style.left = rect.left + "px";
            dropdown.style.width = rect.width + "px";
            dropdown.classList.remove("hidden");

            dropdown.querySelectorAll(".autocomplete-item").forEach(item => {
                item.addEventListener("mousedown", (e) => {
                    e.stopPropagation();
                    inputEl.value = item.textContent.trim();
                    dropdown.classList.add("hidden");
                    setTimeout(() => dropdown.innerHTML = "", 50);
                });
            });
        }

        inputEl.addEventListener("input", show);
        inputEl.addEventListener("focus", show);

        return dropdown;
    }

    const depInput = overlay.querySelector("#edit_departure");
    const dstInput = overlay.querySelector("#edit_destination");

    const depDropdown = bindWarehouseAutocomplete(depInput);
    const dstDropdown = bindWarehouseAutocomplete(dstInput);

    const onDocDown = (e) => {
        if (e.target.closest(".autocomplete-item")) return;
        if (!depDropdown.contains(e.target) && e.target !== depInput) depDropdown.classList.add("hidden");
        if (!dstDropdown.contains(e.target) && e.target !== dstInput) dstDropdown.classList.add("hidden");
    };
    document.addEventListener("mousedown", onDocDown);

    function cleanup() {
        document.removeEventListener("mousedown", onDocDown);
        overlay.remove();
    }

    // ----------------------------
    // buttons
    // ----------------------------
    document.getElementById("edit_cancel").onclick = cleanup;

    document.getElementById("edit_save").onclick = async () => {

        const payload = {
            // справочники (сохраняем ссылки/ID)
            warehouse_id: document.getElementById("edit_warehouse").value || null,
            cargo_type_id: document.getElementById("edit_cargo_type").value || null,
            cargo_status_id: document.getElementById("edit_cargo_status").value || null,
            packaging_type_id: document.getElementById("edit_packaging").value || null,

            // обычные поля
            cargo_description: document.getElementById("edit_description").value.trim(),
            // TODO: after backend migration to FK (departure_warehouse_id / destination_warehouse_id),
            // TODO: store IDs instead of text and set these inputs based on returned warehouse objects.
            departure_place: depInput.value.trim(),      // сейчас в модели это строка
            destination_place: dstInput.value.trim(),    // сейчас в модели это строка
            weight: document.getElementById("edit_weight").value || null,
            volume: document.getElementById("edit_volume").value || null,
            cost: document.getElementById("edit_cost").value || null,
            delivery_time: document.getElementById("edit_delivery_time").value || null,
            shipping_date: document.getElementById("edit_shipping_date").value || null,
            delivery_date: document.getElementById("edit_delivery_date").value || null,
            comment: document.getElementById("edit_comment").value.trim(),
        };

        await fetch(`/api/products-table/${product.id}/`, {
            method: "PUT",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRF(),
            },
            body: JSON.stringify(payload)
        });

        cleanup();
        PT_reset();
        PT_load();
    };
}



function stubCalcFinance(product) {
    alert("ЗАГЛУШКА: расчет финансов для товара ID " + product.id);
}
