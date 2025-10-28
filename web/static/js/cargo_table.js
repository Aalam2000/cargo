// web/static/js/cargo_table.js

const tableConfig = {
    tableId: "cargo-table",
    apiPath: "/api/cargo_table/data/",
    configPath: "/api/cargo_table/config/",
    saveSettingsPath: "/cargo_acc/api/save_table_settings/",
    limit: 50,
};

let offset = 0;
let hasMore = true;
let loading = false;
let filters = {};
let userConfig = null;

let currentRows = []; // хранить текущие данные таблицы

const USER_ROLE = window.CARGO_USER_ROLE || "Guest";
const CLIENT_CODE = window.CLIENT_CODE || "";

// === ЛОГ ===
function log(...args) {
    console.log("[CargoTable]", ...args);
    sendLog(args.join(" "));
}

async function sendLog(msg) {
    try {
        await fetch("/api/log/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({source: "cargo_table.js", message: msg}),
        });
    } catch (e) {
        console.warn("Не удалось отправить лог:", e);
    }
}

// === API ===
async function fetchUserConfig() {
    try {
        const res = await fetch(tableConfig.configPath);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const cfg = await res.json();
        // ✅ если пришло мало полей — дополним стандартными
        if (!cfg.columns || cfg.columns.length < 8) {
            cfg.columns = [
                {"field": "cargo_code", "label": "Код", "visible": true},
                {"field": "cargo_description", "label": "Описание", "visible": true},
                {"field": "client", "label": "Клиент", "visible": true},
                {"field": "status", "label": "Статус", "visible": true},
                {"field": "packaging", "label": "Упаковка", "visible": true},
                {"field": "weight", "label": "Вес", "visible": true},
                {"field": "volume", "label": "Объём", "visible": true},
                {"field": "cost", "label": "Стоимость", "visible": true},
            ];
            cfg.page_size = 50;
        }
        return cfg;
    } catch (e) {
        return null;
    }
}

async function fetchCargoData(reset = false) {
    if (loading) return;
    if (reset) {
        offset = 0;
        hasMore = true;
        document.getElementById("cargo-body").innerHTML = "";
    }
    if (!hasMore) return;

    loading = true;
    document.getElementById("loader").style.display = "block";

    const params = new URLSearchParams({offset, limit: tableConfig.limit, ...filters});
    if (USER_ROLE === "Client" && CLIENT_CODE) params.set("client", CLIENT_CODE);

    try {
        const res = await fetch(`${tableConfig.apiPath}?${params.toString()}`);
        if (!res.ok) throw new Error(`Ошибка загрузки данных ${res.status}`);
        const data = await res.json();

        const rows = data.results || [];
        renderRows(rows);
        offset += rows.length;
        hasMore = data.has_more;
    } catch (e) {
        log("❌ Ошибка загрузки данных:", e);
    } finally {
        loading = false;
        document.getElementById("loader").style.display = hasMore ? "block" : "none";
    }
}

// === Таблица ===
function renderHeader(columns) {
    const headerRow = document.getElementById("cargo-header-row");
    if (!headerRow) {
        log("❌ Не найден #cargo-header-row");
        return;
    }

    headerRow.innerHTML = "";
    columns.filter(col => col.visible).forEach((col, index) => {
        const th = document.createElement("th");
        th.textContent = col.label;
        th.draggable = true;
        th.dataset.index = index;
        headerRow.appendChild(th);
    });

    // === Drag-n-drop ===
    let dragStartIndex = null;
    headerRow.querySelectorAll("th").forEach(th => {
        th.addEventListener("dragstart", e => {
            dragStartIndex = parseInt(th.dataset.index);
            th.classList.add("dragging");
        });
        th.addEventListener("dragend", e => {
            th.classList.remove("dragging");
        });
    });

    headerRow.addEventListener("dragover", e => e.preventDefault());
    headerRow.addEventListener("drop", e => {
        const dropTarget = e.target.closest("th");
        if (!dropTarget || dragStartIndex === null) return;
        const dropIndex = parseInt(dropTarget.dataset.index);
        if (dropIndex === dragStartIndex) return;

        moveColumn(dragStartIndex, dropIndex);
        renderHeader(userConfig.columns);
        renderRows(currentRows || []);
    });

}


function renderRows(rows) {
    const tbody = document.getElementById("cargo-body");
    if (!tbody) {
        log("❌ Не найден #cargo-body");
        return;
    }
    currentRows = rows;

    const frag = document.createDocumentFragment();
    rows.forEach((row, i) => {
        const tr = document.createElement("tr");
        userConfig.columns.forEach(col => {
            if (!col.visible) return;
            const td = document.createElement("td");
            td.textContent = row[col.field] ?? "";
            tr.appendChild(td);
        });
        frag.appendChild(tr);
    });
    tbody.appendChild(frag);
}


function moveColumn(fromIndex, toIndex) {
    const cols = userConfig.columns;
    const visibleCols = cols.filter(c => c.visible);
    const hiddenCols = cols.filter(c => !c.visible);
    const movingCol = visibleCols.splice(fromIndex, 1)[0];
    visibleCols.splice(toIndex, 0, movingCol);
    // сохраняем итоговый порядок
    userConfig.columns = [...visibleCols, ...hiddenCols];
}


// === Фильтры ===
function setupFilters() {
    document.querySelectorAll(".filter-container input").forEach(inp => {
        inp.addEventListener("input", () => {
            filters[inp.id.replace("filter-", "")] = inp.value;
            fetchCargoData(true);
        });
    });
}

function setupDynamicFilters() {
    const filterContainer = document.querySelector(".filter-container");
    if (!filterContainer) return;

    filterContainer.innerHTML = "";
    const fields = USER_ROLE === "Client"
        ? [
            { id: "filter-cargo", placeholder: "Груз..." },
            { id: "filter-shipping_date", placeholder: "Дата отправки..." },
            { id: "filter-delivery_date", placeholder: "Дата доставки..." },
          ]
        : [
            { id: "filter-cargo", placeholder: "Груз..." },
            { id: "filter-client", placeholder: "Клиент..." },
            { id: "filter-shipping_date", placeholder: "Дата отправки..." },
            { id: "filter-delivery_date", placeholder: "Дата доставки..." },
          ];

    fields.forEach(f => {
        const input = document.createElement("input");
        input.type = "text";
        input.id = f.id;
        input.placeholder = f.placeholder;
        input.classList.add("filter-input");
        input.addEventListener("input", () => {
            filters[f.id.replace("filter-", "")] = input.value;
            fetchCargoData(true);
        });
        filterContainer.appendChild(input);
    });
}



// === Модалка ===
function openSettingsModal() {
    const modal = document.getElementById("settings-modal");
    const overlay = document.getElementById("modal-overlay");
    const form = document.getElementById("settings-form");

    if (!modal || !overlay || !form) {
        log("❌ Не найдены элементы модалки");
        return;
    }

    form.innerHTML = "";

    userConfig.columns.forEach((col, idx) => {
        const div = document.createElement("div");
        div.classList.add("setting-row");
        div.draggable = true;
        div.dataset.index = idx;

        const dragHandle = document.createElement("span");
        dragHandle.textContent = "☰";
        dragHandle.classList.add("drag-handle");

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = col.field;
        checkbox.checked = col.visible;

        const label = document.createElement("label");
        label.htmlFor = col.field;
        label.textContent = col.label;

        div.appendChild(dragHandle);
        div.appendChild(checkbox);
        div.appendChild(label);
        form.appendChild(div);
    });

    // drag-n-drop внутри модалки
    let dragged = null;
    form.addEventListener("dragstart", e => {
        dragged = e.target.closest(".setting-row");
        dragged.classList.add("dragging");
    });
    form.addEventListener("dragover", e => e.preventDefault());
    form.addEventListener("drop", e => {
        e.preventDefault();
        const target = e.target.closest(".setting-row");
        if (!target || target === dragged) return;
        const rows = [...form.querySelectorAll(".setting-row")];
        const draggedIndex = rows.indexOf(dragged);
        const targetIndex = rows.indexOf(target);
        if (draggedIndex > targetIndex) {
            form.insertBefore(dragged, target);
        } else {
            form.insertBefore(dragged, target.nextSibling);
        }
    });
    form.addEventListener("dragend", e => {
        e.target.classList.remove("dragging");
    });

    overlay.style.display = "block";
    modal.style.display = "block";
    overlay.classList.add("show");
    modal.classList.add("show");
}


function closeSettingsModal() {
    const modal = document.getElementById("settings-modal");
    const overlay = document.getElementById("modal-overlay");

    modal.classList.remove("show");
    overlay.classList.remove("show");
    modal.style.display = "none";
    overlay.style.display = "none";
}

async function saveSettings() {
    const rows = document.querySelectorAll("#settings-form .setting-row");
    const newOrder = [];

    rows.forEach(row => {
        const field = row.querySelector("input").id;
        const checked = row.querySelector("input").checked;
        const col = userConfig.columns.find(c => c.field === field);
        if (col) {
            col.visible = checked;
            newOrder.push(col);
        }
    });

// обновляем порядок
    userConfig.columns = newOrder;

    try {
        function getCSRFToken() {
            const match = document.cookie.match(/csrftoken=([^;]+)/);
            return match ? match[1] : "";
        }

        const res = await fetch(tableConfig.saveSettingsPath, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
            credentials: "include",
            body: JSON.stringify({cargo_table: userConfig}),
        });
    } catch (e) {
        log("❌ Ошибка сохранения настроек:", e);
    }


    closeSettingsModal();
    renderHeader(userConfig.columns);
    fetchCargoData(true);
    // === ПАГИНАЦИЯ ===
    const wrapper = document.querySelector(".table-wrapper");
    if (wrapper) {
        wrapper.addEventListener("scroll", () => {
            const nearBottom =
                wrapper.scrollTop + wrapper.clientHeight >= wrapper.scrollHeight - 40;
            if (nearBottom && hasMore && !loading) {
                fetchCargoData();
            }
        });
    }

}

// === Init ===
document.addEventListener("DOMContentLoaded", async () => {
    userConfig = await fetchUserConfig();

    if (!userConfig || !userConfig.columns) {
        log("❌ Конфигурация таблицы не получена");
        return;
    }

    renderHeader(userConfig.columns);

    // === Фильтры по ролям ===
    setupDynamicFilters();
    setupFilters();

    fetchCargoData();


    document.getElementById("settings-btn").addEventListener("click", openSettingsModal);
    document.getElementById("settings-cancel").addEventListener("click", closeSettingsModal);
    document.getElementById("settings-save").addEventListener("click", saveSettings);

    const overlay = document.getElementById("modal-overlay");
    if (overlay) overlay.addEventListener("click", closeSettingsModal);
    // кнопка "Сохранить порядок" в модалке
    const saveBtn = document.getElementById("settings-save");
    if (saveBtn) {
        saveBtn.addEventListener("click", saveSettings);
    }
});
