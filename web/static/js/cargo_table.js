// web/static/js/cargo_table.js
// ================================
//   CARGOS TABLE — lazy (как товары)
//   Работает с /api/cargos_table/
// ================================

(function () {
    const CT_API = "/api/cargos_table/";

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

        const res = await fetch(url, {credentials: "same-origin"});
        return await res.json();
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
            CT_buildHeader(); // шапка должна быть даже когда строк 0
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

    document.addEventListener("DOMContentLoaded", () => {
        CT_bindFilters();
        CT_bindScroll();
        CT_reset();
        CT_load();
    });
})();
