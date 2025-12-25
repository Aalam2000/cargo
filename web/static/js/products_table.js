// ================================
//   PRODUCTS TABLE — новая версия
//   Работает с /api/products-table/
// ================================

const PT_API = "/api/products-table/";

let PT_sortBy = "product_code";
let PT_sortDir = "asc";

const PT_lazy = {
    offset: 0,
    limit: 30,
    loading: false,
    finished: false
};

// поля таблицы (строго по ТЗ)
const PT_COLUMNS = [
    {field: "product_code", label: "Код товара", sortable: true},
    {field: "client", label: "Клиент", sortable: true},
    {field: "cargo", label: "Груз", sortable: true},
    {field: "cargo_status", label: "Статус", sortable: false},
    {field: "warehouse", label: "Склад", sortable: true},
    {field: "weight", label: "Вес", sortable: false},
    {field: "volume", label: "Объём", sortable: false},
    {field: "cost", label: "Стоимость", sortable: false},
    {field: "images", label: "Фото", sortable: false},
];

// ========================
//  FETCH
// ========================
async function PT_fetch() {
    const url = new URL(PT_API, window.location.origin);

    url.searchParams.set("offset", PT_lazy.offset);
    url.searchParams.set("limit", PT_lazy.limit);

    url.searchParams.set("sort_by", PT_sortBy);
    url.searchParams.set("sort_dir", PT_sortDir);

    // фильтры
    const f_code = document.getElementById("filterProductCode").value.trim();
    const f_client = document.getElementById("filterClient").value.trim();
    const f_cargo = document.getElementById("filterCargo").value.trim();
    const f_warehouse = document.getElementById("filterWarehouse").value.trim();

    if (f_code) url.searchParams.set("filter[product_code]", f_code);
    if (f_client) url.searchParams.set("filter[client]", f_client);
    if (f_cargo) url.searchParams.set("filter[cargo]", f_cargo);
    if (f_warehouse) url.searchParams.set("filter[warehouse]", f_warehouse);


    const res = await fetch(url);
    return await res.json();
}

// ========================
//  TABLE HEADER
// ========================
function PT_buildHeader() {
    const thead = document.getElementById("product-head");
    thead.innerHTML = "";

    let tr = document.createElement("tr");

    PT_COLUMNS.forEach(col => {
        const th = document.createElement("th");
        th.textContent = col.label;

        if (col.sortable) {
            th.classList.add("sortable");
            th.dataset.field = col.field;

            th.addEventListener("click", () => {
                if (PT_sortBy === col.field) {
                    PT_sortDir = PT_sortDir === "asc" ? "desc" : "asc";
                } else {
                    PT_sortBy = col.field;
                    PT_sortDir = "asc";
                }
                PT_reset();
                PT_load();
            });
        }

        tr.appendChild(th);
    });

    thead.appendChild(tr);
}

// ========================
//  TABLE ROWS
// ========================
function PT_appendRows(items) {
    const tbody = document.getElementById("product-body");

    items.forEach(p => {
        const tr = document.createElement("tr");
        tr.dataset.id = p.id || "";

        PT_COLUMNS.forEach(col => {
            let v = p[col.field];

            if (col.field === "images") {
                v = Array.isArray(v) ? `${v.length} шт.` : "";
            }

            const td = document.createElement("td");
            td.textContent = v ?? "";
            tr.appendChild(td);
        });

        tr.addEventListener("click", () => {
            loadFullProductAndEdit(p.id);
        });

        tbody.appendChild(tr);
    });
}

// ========================
//  RESET TABLE
// ========================
function PT_reset() {
    PT_lazy.offset = 0;
    PT_lazy.loading = false;
    PT_lazy.finished = false;
    document.getElementById("product-body").innerHTML = "";
}

// ========================
//  LOAD (lazy)
// ========================
async function PT_load() {
    if (PT_lazy.loading || PT_lazy.finished) return;
    PT_lazy.loading = true;

    document.getElementById("product-loader").classList.remove("hidden");
    document.getElementById("product-empty").classList.add("hidden");

    const data = await PT_fetch();

    if (!data.results || data.results.length === 0) {
        if (PT_lazy.offset === 0) {
            document.getElementById("product-empty").classList.remove("hidden");
        }
        PT_lazy.finished = true;
        document.getElementById("product-loader").classList.add("hidden");
        return;
    }

    if (PT_lazy.offset === 0) {
        PT_buildHeader();
    }

    PT_appendRows(data.results);

    PT_lazy.offset += PT_lazy.limit;

    if (!data.has_more) PT_lazy.finished = true;

    document.getElementById("product-loader").classList.add("hidden");
    PT_lazy.loading = false;
}

// ========================
//  FILTER EVENTS
// ========================
function PT_bindFilters() {
    const inputs = [
        "filterProductCode",
        "filterClient",
        "filterCargo",
        "filterWarehouse"
    ];

    inputs.forEach(id => {
        document.getElementById(id).addEventListener("input", () => {
            PT_reset();
            PT_load();
        });
    });
}

// ========================
//  SCROLL (lazy)
// ========================
function PT_bindScroll() {
    const wrap = document.getElementById("product-table-wrapper");

    wrap.addEventListener("scroll", () => {
        if (wrap.scrollTop + wrap.clientHeight >= wrap.scrollHeight - 200) {
            PT_load();
        }
    });
}

// ========================
//  INIT
// ========================
document.addEventListener("DOMContentLoaded", () => {

    document.getElementById("btnAddProduct")
        .addEventListener("click", () => openProductAdd()); // модалка под добавление

    PT_bindFilters();
    PT_bindScroll();

    PT_reset();
    PT_load();
});
