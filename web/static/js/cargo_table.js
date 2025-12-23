// web/static/js/cargo_table.js
// ================================
//   CARGOS TABLE — lazy (как товары)
//   Работает с /api/cargos_table/
//   + MODAL: создать груз из товаров выбранного клиента
// ================================
function renderAddCargoModal(isEdit = false) {
    return `
        <div class="modal-header">
            <h3>${isEdit ? "Редактировать груз" : "Добавить груз"}</h3>
            <button class="modal-close" id="cargoModalClose">✖</button>
        </div>

        <div class="modal-body">
            <div class="select-search-wrapper">
                <input
                    type="text"
                    id="addCargoClientInput"
                    class="modal-input select-search-input"
                    placeholder="Начните ввод клиента"
                    autocomplete="off"
                    ${isEdit ? "disabled" : ""}
                >
                <div id="addCargoClientList" class="autocomplete-list hidden"></div>
            </div>

            <table class="table">
                <thead>
                    <tr>
                        <th>Код</th>
                        <th>Описание</th>
                        <th>Стоимость</th>
                    </tr>
                </thead>
                <tbody id="addCargoProductsTbody"></tbody>
            </table>

            <button id="editProductsBtn" class="btn-secondary">
                Изменить товары
            </button>

            <div id="addCargoError" class="error-text"></div>
        </div>

        <div class="modal-footer">
            <button id="addCargoCancelBtn" class="btn-secondary">Отмена</button>
            <button id="addCargoSaveBtn" class="btn-primary" disabled>
                ${isEdit ? "Сохранить" : "Создать"}
            </button>
        </div>
    `;
}


(function () {
    const CT_API = "/api/cargos_table/";
    const CT_CLIENTS_API = "/api/get_clients/";
    const CT_GENERATE_CARGO_API = "/api/generate/cargo/";

    let CT_sortBy = "cargo_code";
    let CT_sortDir = "asc";

    const CT_lazy = {
        offset: 0,
        limit: 30,
        loading: false,
        finished: false
    };

    const CT_COLUMNS = [
        {field: "client", label: "Клиент", sortable: true},
        {field: "cargo_code", label: "Код груза", sortable: true},
        {field: "record_date", label: "Дата записи", sortable: true},
        {field: "products_count", label: "Товаров", sortable: true},
        {field: "warehouse", label: "Склад", sortable: true},
        {field: "cargo_status", label: "Статус", sortable: true},
        {field: "packaging_type", label: "Упаковка груза", sortable: true},
        {field: "weight_total", label: "Вес итого", sortable: true},
        {field: "volume_total", label: "Объём итого", sortable: true},
        {field: "is_locked", label: "Состав фикс.", sortable: true},
    ];

    // ------------------------------
    // helpers
    // ------------------------------

    function CT_getRole() {
        const meta = document.querySelector('meta[name="user-role"]');
        return (meta && meta.content) ? meta.content : "";
    }

    function CT_show(el) {
        el.classList.remove("hidden");
    }

    function CT_hide(el) {
        el.classList.add("hidden");
    }

    async function CT_json(url, opts) {
        const res = await fetch(url, {
            credentials: "same-origin",
            headers: {
                ...(opts && opts.headers ? opts.headers : {}),
                "Content-Type": "application/json",
            },
            ...opts,
        });

        const text = await res.text();
        let data = null;
        try {
            data = text ? JSON.parse(text) : null;
        } catch (e) {
            throw new Error("bad json");
        }

        if (!res.ok) {
            const msg = (data && (data.error || data.detail)) ? (data.error || data.detail) : ("HTTP " + res.status);
            throw new Error(msg);
        }
        return data;
    }

    function CT_getCsrfToken() {
        // Django default cookie name
        const m = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : "";
    }

    // ------------------------------
    // table
    // ------------------------------

    async function CT_fetch() {
        const url = new URL(CT_API, window.location.origin);

        url.searchParams.set("offset", CT_lazy.offset);
        url.searchParams.set("limit", CT_lazy.limit);

        url.searchParams.set("sort_by", CT_sortBy);
        url.searchParams.set("sort_dir", CT_sortDir);

        const f_cargo = document.getElementById("filterCargoCode").value.trim();
        const f_client = document.getElementById("filterClient").value.trim();
        const f_warehouse = document.getElementById("filterWarehouse").value.trim();
        const f_status = document.getElementById("filterStatus").value.trim();

        if (f_cargo) url.searchParams.set("filter[cargo_code]", f_cargo);
        if (f_client) url.searchParams.set("filter[client]", f_client);
        if (f_warehouse) url.searchParams.set("filter[warehouse]", f_warehouse);
        if (f_status) url.searchParams.set("filter[cargo_status]", f_status);

        return await CT_json(url);
    }

    function CT_buildHeader() {
        const thead = document.getElementById("cargos_head");
        thead.innerHTML = "";

        const tr = document.createElement("tr");

        CT_COLUMNS.forEach(col => {
            const th = document.createElement("th");
            th.textContent = col.label;

            if (col.sortable) {
                th.classList.add("sortable");
                th.dataset.field = col.field;

                th.addEventListener("click", () => {
                    if (CT_sortBy === col.field) {
                        CT_sortDir = CT_sortDir === "asc" ? "desc" : "asc";
                    } else {
                        CT_sortBy = col.field;
                        CT_sortDir = "asc";
                    }
                    CT_reset();
                    CT_load();
                });
            }

            tr.appendChild(th);
        });

        thead.appendChild(tr);
    }

    function CT_appendRows(items) {
        const tbody = document.getElementById("tbody_cargos");

        items.forEach(c => {
            const tr = document.createElement("tr");
            tr.dataset.id = c.id || "";
            tr.addEventListener("click", () => {
                AC_openEditModal(c.id);
            });

            CT_COLUMNS.forEach(col => {
                let v = c[col.field];
                if (col.field === "is_locked") {
                    v = v ? "Да" : "Нет";
                }
                const td = document.createElement("td");
                td.textContent = v ?? "";
                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });
    }

    async function AC_openProductsSelector() {
        const url = new URL(CT_API, window.location.origin);
        url.searchParams.set("mode", "cargo_products");
        url.searchParams.set("client_id", AC_state.clientId);
        if (AC_state.cargoId) {
            url.searchParams.set("cargo_id", AC_state.cargoId);
        }

        const data = await CT_json(url);
        const items = [...data.selected, ...data.free];

        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>Товары клиента</h3>
                    <button class="modal-close" id="closeSelect">✖</button>
                </div>
                <div class="modal-body">
                    <table class="table">
                        <tbody>
                            ${items.map(p => `
                                <tr>
                                    <td>
                                        <input type="checkbox" data-id="${p.id}"
                                        ${AC_state.selectedProductIds.has(p.id) ? "checked" : ""}>
                                    </td>
                                    <td>${p.product_code}</td>
                                    <td>${p.cargo_description || ""}</td>
                                    <td>${p.cost ?? ""}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
                <div class="modal-footer">
                    <button id="applyProducts" class="btn-primary">Сохранить</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.querySelector("#closeSelect").onclick = () => overlay.remove();

        overlay.querySelector("#applyProducts").onclick = () => {
            AC_state.selectedProductIds.clear();
            overlay.querySelectorAll("input[type=checkbox]").forEach(cb => {
                if (cb.checked) AC_state.selectedProductIds.add(Number(cb.dataset.id));
            });

            const selected = items.filter(p => AC_state.selectedProductIds.has(p.id));
            AC_renderSelectedProducts(selected);
            AC_refreshSaveEnabled();
            overlay.remove();
        };
    }

    function AC_renderSelectedProducts(items) {
        const tbody = AC_el("addCargoProductsTbody");
        tbody.innerHTML = "";

        items.forEach(p => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${p.product_code}</td>
                <td>${p.cargo_description || ""}</td>
                <td>${p.cost ?? ""}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    async function AC_openEditModal(cargoId) {
        AC_state.mode = "edit";
        AC_state.cargoId = cargoId;
        AC_state.selectedProductIds = new Set();

        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.innerHTML = `
            <div class="modal">
                ${renderAddCargoModal(true)}
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.querySelector("#cargoModalClose").onclick =
            overlay.querySelector("#addCargoCancelBtn").onclick =
                () => overlay.remove();

        overlay.querySelector("#addCargoSaveBtn").onclick = AC_save;

        // груз → клиент + товары
        const url = new URL(CT_API, window.location.origin);
        url.searchParams.set("mode", "cargo_products");
        url.searchParams.set("cargo_id", cargoId);

        const data = await CT_json(url);

        AC_state.clientId = String(data.client_id || "");

        const clientInput = document.getElementById("addCargoClientInput");
        if (clientInput) {
            clientInput.value = data.client_code || "";
        }


        // выбранные
        AC_state.selectedProductIds.clear();
        data.selected.forEach(p => {
            AC_state.selectedProductIds.add(Number(p.id));
        });

        AC_renderSelectedProducts(data.selected);
        AC_refreshSaveEnabled();
        const editBtn = overlay.querySelector("#editProductsBtn");
        editBtn.onclick = () => {
            AC_openProductsSelector();
        };

    }

    function CT_reset() {
        CT_lazy.offset = 0;
        CT_lazy.loading = false;
        CT_lazy.finished = false;
        document.getElementById("tbody_cargos").innerHTML = "";
    }

    async function CT_load() {
        if (CT_lazy.loading || CT_lazy.finished) return;
        CT_lazy.loading = true;

        document.getElementById("loader_cargos").classList.remove("hidden");

        const data = await CT_fetch();

        if (CT_lazy.offset === 0) {
            CT_buildHeader();
        }

        if (!data.results || data.results.length === 0) {
            CT_lazy.finished = true;
            document.getElementById("loader_cargos").classList.add("hidden");
            CT_lazy.loading = false;
            return;
        }

        CT_appendRows(data.results);
        CT_lazy.offset += CT_lazy.limit;
        if (!data.has_more) CT_lazy.finished = true;

        document.getElementById("loader_cargos").classList.add("hidden");
        CT_lazy.loading = false;
    }

    function CT_bindFilters() {
        ["filterCargoCode", "filterClient", "filterWarehouse", "filterStatus"].forEach(id => {
            document.getElementById(id).addEventListener("input", () => {
                CT_reset();
                CT_load();
            });
        });
    }

    function CT_bindScroll() {
        const wrap = document.querySelector('.table-wrapper[data-table-key="cargos"]');
        if (!wrap) return;
        wrap.addEventListener("scroll", () => {
            if (wrap.scrollTop + wrap.clientHeight >= wrap.scrollHeight - 200) {
                CT_load();
            }
        });
    }

    // ------------------------------
    // modal: add cargo
    // ------------------------------

    const AC_state = {
        mode: "create",          // create | edit
        cargoId: null,
        clientId: "",
        selectedProductIds: new Set(),
    };

    // ------------------------------
    // client autocomplete
    // ------------------------------
    let AC_clientPage = 1;
    let AC_clientSearch = "";
    let AC_clientLoading = false;

    async function AC_fetchClients(search, page = 1) {
        const url = new URL("/api/get_clients/", window.location.origin);
        url.searchParams.set("search", search);
        url.searchParams.set("page", page);
        url.searchParams.set("page_size", 7);
        return await CT_json(url);
    }

    function AC_clearClientList() {
        const list = document.getElementById("addCargoClientList");
        if (!list) return;
        list.innerHTML = "";
        list.classList.add("hidden");
    }

    function AC_renderClientList(items) {
        const list = document.getElementById("addCargoClientList");
        list.innerHTML = "";

        if (!items.length) {
            const empty = document.createElement("div");
            empty.className = "autocomplete-empty";
            empty.textContent = "Ничего не найдено";
            list.appendChild(empty);
            list.classList.remove("hidden");
            return;
        }

        items.forEach(c => {
            const div = document.createElement("div");
            div.className = "autocomplete-item";
            div.textContent = c.client_code;
            div.dataset.id = c.id;

            div.onclick = async () => {
                document.getElementById("addCargoClientInput").value = c.client_code;
                AC_state.clientId = String(c.id);
                AC_clearClientList();
            };

            list.appendChild(div);
        });

        list.classList.remove("hidden");
    }


    function AC_el(id) {
        return document.getElementById(id);
    }

    function AC_setError(msg) {
        AC_el("addCargoError").textContent = msg || "";
    }

    function AC_resetModal() {
        AC_setError("");
        AC_state.clientId = "";
        AC_state.products = [];
        AC_state.productsById = {};

        const clientInput = AC_el("addCargoClientInput");
        if (clientInput) clientInput.value = "";

        AC_el("addCargoProductsTbody").innerHTML = "";
        AC_el("addCargoSaveBtn").disabled = true;
    }

    function AC_openModal() {
        // RESET STATE FOR CREATE MODE
        AC_state.mode = "create";
        AC_state.cargoId = null;
        AC_state.clientId = "";
        AC_state.selectedProductIds.clear();

        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";

        overlay.innerHTML = `
            <div class="modal">
                ${renderAddCargoModal()}
            </div>
        `;

        document.body.appendChild(overlay);

        overlay.querySelector("#cargoModalClose").onclick = () => overlay.remove();
        overlay.querySelector("#addCargoCancelBtn").onclick = () => overlay.remove();
        overlay.querySelector("#addCargoSaveBtn").onclick = AC_save;

        const clientInput = document.getElementById("addCargoClientInput");
        const clientList = document.getElementById("addCargoClientList");

        clientInput.addEventListener("input", async () => {
            const v = clientInput.value.trim();
            AC_state.clientId = "";
            AC_clearClientList();

            if (!v || v.length < 1) return;

            AC_clientSearch = v;
            AC_clientPage = 1;
            AC_clientLoading = true;

            const data = await AC_fetchClients(v, 1);
            AC_renderClientList(data.results || []);

            AC_clientLoading = false;
        });

        document.addEventListener("click", (e) => {
            if (!document.body.contains(clientInput)) return;
            if (!clientInput.contains(e.target) && !clientList.contains(e.target)) {
                AC_clearClientList();
            }
        });

        const editBtn = overlay.querySelector("#editProductsBtn");
        editBtn.onclick = () => {
            if (!AC_state.clientId) {
                AC_setError("Сначала выберите клиента");
                return;
            }
            AC_openProductsSelector();
        };
    }


    function AC_closeModal() {
        CT_hide(AC_el("modal-overlay"));
        CT_hide(AC_el("add-cargo-modal"));
    }

    function AC_refreshSaveEnabled() {
        const ids = Array.from(AC_state.selectedProductIds);
        const canSave = AC_state.clientId && ids.length > 0;
        AC_el("addCargoSaveBtn").disabled = !canSave;

        if (!canSave) {
            AC_setError("Выберите хотя бы один товар");
        } else {
            AC_setError("");
        }
    }


    function AC_addRow() {
        if (!AC_state.clientId) return;
        if (!AC_state.products || AC_state.products.length === 0) return;

        const tbody = AC_el("addCargoProductsTbody");
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td style="min-width:140px;">
                <select data-ac="product" class="input-filter" style="width:100%;"></select>
            </td>
            <td style="min-width:260px;">
                <input data-ac="desc" class="input-filter" style="width:100%;" readonly>
            </td>
            <td style="min-width:140px;">
                <input data-ac="cost" class="input-filter" style="width:100%;" readonly>
            </td>
            <td style="width:42px; text-align:center;">
                <button type="button" data-ac="remove" style="border:0; background:transparent; cursor:pointer; font-size:16px;">✖</button>
            </td>
        `;

        const sel = tr.querySelector("select[data-ac='product']");
        const inpDesc = tr.querySelector("input[data-ac='desc']");
        const inpCost = tr.querySelector("input[data-ac='cost']");
        const btnRemove = tr.querySelector("button[data-ac='remove']");

        sel.addEventListener("change", () => {
            const pid = (sel.value || "").trim();
            const p = pid ? AC_state.productsById[pid] : null;

            inpDesc.value = p && p.cargo_description ? p.cargo_description : "";
            inpCost.value = (p && p.cost !== null && p.cost !== undefined) ? String(p.cost) : "";

            AC_refreshSaveEnabled();
        });

        btnRemove.addEventListener("click", () => {
            tr.remove();
            AC_refreshSaveEnabled();
        });

        tbody.appendChild(tr);

        AC_refreshSaveEnabled();
    }

    async function AC_generateCargoCode() {
        const clientId = AC_state.clientId;
        if (!clientId) throw new Error("client_id required");

        const data = await CT_json(CT_GENERATE_CARGO_API, {
            method: "POST",
            headers: {
                "X-CSRFToken": CT_getCsrfToken(),
            },
            body: JSON.stringify({
                client_id: clientId,
            }),
        });

        if (!data || !data.cargo_code) {
            throw new Error("bad generate response");
        }

        return String(data.cargo_code).trim();
    }


    async function AC_save() {
        AC_setError("");

        const productIds = Array.from(AC_state.selectedProductIds);
        if (!AC_state.clientId || productIds.length === 0) {
            AC_setError("Не выбран клиент или товары");
            return;
        }

        AC_el("addCargoSaveBtn").disabled = true;

        try {
            let payload = {
                client_id: AC_state.clientId,
                product_ids: productIds,
            };

            if (AC_state.mode === "create") {
                payload.cargo_code = await AC_generateCargoCode();
            } else {
                payload.cargo_id = AC_state.cargoId;
            }

            await CT_json(CT_API, {
                method: "POST",
                headers: {"X-CSRFToken": CT_getCsrfToken()},
                body: JSON.stringify(payload),
            });

            document.querySelector(".modal-overlay")?.remove();
            CT_reset();
            CT_load();
        } catch (e) {
            AC_setError(e.message);
            AC_refreshSaveEnabled();
        }
    }


    function CT_bindAddCargoModal() {
        const role = CT_getRole();
        const addBtn = document.getElementById("add-cargo-btn");
        if (!addBtn) return;

        if (role === "Client") {
            addBtn.style.display = "none";
            return;
        }

        addBtn.addEventListener("click", AC_openModal);
    }


    document.addEventListener("DOMContentLoaded", () => {
        CT_bindFilters();
        CT_bindScroll();
        CT_bindAddCargoModal();
        CT_reset();
        CT_load();
    });
})();
