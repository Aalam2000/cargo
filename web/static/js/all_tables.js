/* web/static/js/all_tables.js */

// === Константа только для отображения имён и заголовков ===
const tableMetadata = {
    'cargo': { label: 'Грузы', fields: ['id', 'cargo_code', 'client', 'company', 'weight', 'cost'] },
    'client': { label: 'Клиенты', fields: ['id', 'client_code', 'company', 'description'] },
    'company': { label: 'Компании', fields: ['id', 'name', 'registration', 'description'] },
    'warehouse': { label: 'Склады', fields: ['id', 'name', 'address', 'company'] },
    'cargotype': { label: 'Типы грузов', fields: ['id', 'name', 'description'] },
    'cargostatus': { label: 'Статусы грузов', fields: ['id', 'name', 'description'] },
    'packagingtype': { label: 'Типы упаковок', fields: ['id', 'name', 'description'] },
    'image': { label: 'Изображения', fields: ['id', 'image_file', 'upload_date'] },
    'vehicle': { label: 'Автотранспорт', fields: ['id', 'license_plate', 'model', 'carrier_company'] },
    'carriercompany': { label: 'Перевозчики', fields: ['id', 'name', 'address'] },
    'transportbill': { label: 'Транспортные накладные', fields: ['id', 'bill_code', 'vehicle', 'departure_place'] },
    'product': { label: 'Товары', fields: ['id', 'product_code', 'client', 'company', 'warehouse'] },
    'cargomovement': { label: 'Перемещения', fields: ['id', 'cargo', 'from_location', 'to_location', 'movement_date'] },
    'cargo_products': { label: 'Связь: Грузы ↔ Товары', fields: ['id', 'cargo', 'product'] },
    'product_images': { label: 'Связь: Товары ↔ Изображения', fields: ['id', 'product', 'image'] },
    'cargo_images': { label: 'Связь: Грузы ↔ Изображения', fields: ['id', 'cargo', 'image'] },
    'transportbill_cargos': { label: 'Связь: Накладные ↔ Грузы', fields: ['id', 'transport_bill', 'cargo'] }
};


// === Универсальный рендер таблиц ===
document.addEventListener("DOMContentLoaded", async () => {
    const container = document.getElementById("tables-container");
    if (!container) return;

    const resp = await fetch("/api/all_tables/");
    const dbTables = await resp.json();

    const knownTables = [];
    const otherTables = [];

    dbTables.forEach(tbl => {
        if (tableMetadata[tbl]) knownTables.push(tbl);
        else otherTables.push(tbl);
    });


    // Создаём секции для известных таблиц
    knownTables.forEach(tbl => container.appendChild(createTableSection(tbl, true)));

    // Добавляем кнопку для прочих таблиц
    if (otherTables.length > 0) {
        const btnBlock = document.createElement("div");
        btnBlock.style.textAlign = "center";
        btnBlock.style.marginTop = "20px";

        const btn = document.createElement("button");
        btn.className = "btn-table";
        btn.textContent = "📂 Прочие таблицы";
        btn.dataset.state = "collapsed";

        const hidden = document.createElement("div");
        hidden.id = "other-tables";
        hidden.style.display = "none";
        hidden.style.marginTop = "20px";

        btn.addEventListener("click", () => {
            const expanded = btn.dataset.state === "expanded";
            hidden.style.display = expanded ? "none" : "block";
            btn.textContent = expanded ? "📂 Прочие таблицы" : "📁 Свернуть прочие таблицы";
            btn.dataset.state = expanded ? "collapsed" : "expanded";
        });

        btnBlock.appendChild(btn);
        container.appendChild(btnBlock);
        container.appendChild(hidden);

        otherTables.forEach(tbl => hidden.appendChild(createTableSection(tbl, false)));
    }

    // Кнопки раскрытия
    document.querySelectorAll(".toggle-table").forEach(btn => {
        btn.addEventListener("click", async () => {
            const table = btn.dataset.table;
            const wrap = document.getElementById(`wrap-${table}`);
            const inner = wrap.querySelector(".inner-table");

            if (btn.dataset.state === "collapsed") {
                btn.textContent = "Свернуть";
                btn.dataset.state = "expanded";
                wrap.style.display = "block";

                if (!inner.innerHTML.trim()) {
                    inner.innerHTML = "<p style='padding:10px;'>Загрузка...</p>";
                    try {
                        // ✅ Исправлены имена API
                        let apiName;
                        if (table === "cargomovement") apiName = "cargo-movements";
                        else if (table === "cargostatus") apiName = "cargo-statuses";
                        else if (table === "cargotype") apiName = "cargo-types";
                        else if (table === "packagingtype") apiName = "packaging-types";
                        else if (table === "carriercompany") apiName = "carrier-companies";
                        else if (table === "transportbill") apiName = "transport-bills";
                        else if (table === "company") apiName = "companies";
                        else if (table === "cargo_products") apiName = "cargos";
                        else if (table === "product_images") apiName = "products";
                        else if (table === "cargo_images") apiName = "cargos";
                        else if (table === "transportbill_cargos") apiName = "transport-bills";
                        else apiName = `${table}s`;

                        const res = await fetch(`/cargo_acc/api/${apiName}/`);
                        if (!res.ok) throw new Error(`HTTP ${res.status}`);

                        const data = await res.json();
                        const rows = data.results || data || [];

                        if (!rows || rows.length === 0) {
                            inner.innerHTML = "<p style='padding:10px;color:#777;'>Пустая таблица</p>";
                            return;
                        }

                        const columns = tableMetadata[table]?.fields || Object.keys(rows[0] || {});
                        renderUniversalTable(inner, columns, columns, rows.slice(0, 20));

                    } catch (err) {
                        inner.innerHTML = `<p style="color:red;padding:10px;">Ошибка загрузки данных (${err.message})</p>`;
                    }

                }
            } else {
                btn.textContent = "Раскрыть";
                btn.dataset.state = "collapsed";
                wrap.style.display = "none";
            }
        });
    });
});


// === Функции ===

function createTableSection(tableName, isKnown) {
    const section = document.createElement("section");
    section.className = "table-container";

    const label = isKnown ? tableMetadata[tableName].label : tableName;
    section.innerHTML = `
        <div class="table-header-container">
            <h3>${label}</h3>
            <button class="btn-table toggle-table" data-table="${tableName}" data-state="collapsed">Раскрыть</button>
        </div>
        <div class="table-wrapper" id="wrap-${tableName}" style="display:none;">
            <div class="inner-table"></div>
        </div>
    `;
    return section;
}


function renderUniversalTable(target, headers, fields, rows) {
    target.innerHTML = "";

    if (!rows || rows.length === 0) {
        target.innerHTML = "<p style='padding:10px;color:#777;'>Пустая таблица</p>";
        return;
    }

    const tableEl = document.createElement("table");
    tableEl.className = "table";

    const thead = document.createElement("thead");
    thead.innerHTML = `<tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr>`;
    tableEl.appendChild(thead);

    const tbody = document.createElement("tbody");
    rows.forEach((r) => {
        const tr = document.createElement("tr");
        tr.innerHTML = fields.map((f) => `<td>${r[f] ?? ""}</td>`).join("");
        tbody.appendChild(tr);
    });
    tableEl.appendChild(tbody);

    target.appendChild(tableEl);
}
