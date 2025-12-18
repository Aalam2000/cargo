// web/static/js/cargo_table.js
(function () {
  const API_URL = "/api/cargos_table/";

  const state = {
    limit: 50,
    offset: 0,
    sort_by: "cargo_code",
    sort_dir: "asc",
    search: ""
  };

  function qs(sel) { return document.querySelector(sel); }
  function esc(s) { return (s ?? "").toString(); }

  function buildQuery() {
    const p = new URLSearchParams();
    p.set("limit", String(state.limit));
    p.set("offset", String(state.offset));
    p.set("sort_by", state.sort_by);
    p.set("sort_dir", state.sort_dir);
    if (state.search) p.set("search", state.search);
    return "?" + p.toString();
  }

  function setLoader(on) {
    const el = qs("#loader_cargos");
    if (!el) return;
    el.classList.toggle("hidden", !on);
  }

  function renderHead() {
    const thead = qs("#cargos_head");
    if (!thead) return;

    const cols = [
      { key: "cargo_code", title: "Код груза" },
      { key: "record_date", title: "Дата записи" },
      { key: "products_count", title: "Товаров" },
      { key: "warehouse", title: "Склад" },
      { key: "cargo_status", title: "Статус" },
      { key: "packaging_type", title: "Упаковка груза" },
      { key: "weight_total", title: "Вес итого" },
      { key: "volume_total", title: "Объём итого" },
      { key: "is_locked", title: "Состав фикс." }
    ];

    const tr = document.createElement("tr");
    cols.forEach(c => {
      const th = document.createElement("th");
      th.textContent = c.title;
      th.dataset.colKey = c.key;
      th.classList.add("sortable");
      th.addEventListener("click", () => {
        if (state.sort_by === c.key) {
          state.sort_dir = (state.sort_dir === "asc") ? "desc" : "asc";
        } else {
          state.sort_by = c.key;
          state.sort_dir = "asc";
        }
        state.offset = 0;
        load();
      });
      tr.appendChild(th);
    });

    thead.innerHTML = "";
    thead.appendChild(tr);
  }

  function renderRows(rows) {
    const tbody = qs("#tbody_cargos");
    if (!tbody) return;

    tbody.innerHTML = "";
    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${esc(r.cargo_code)}</td>
        <td>${esc(r.record_date)}</td>
        <td>${esc(r.products_count)}</td>
        <td>${esc(r.warehouse)}</td>
        <td>${esc(r.cargo_status)}</td>
        <td>${esc(r.packaging_type)}</td>
        <td>${esc(r.weight_total)}</td>
        <td>${esc(r.volume_total)}</td>
        <td>${r.is_locked ? "Да" : "Нет"}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderPager(total, has_more) {
    const info = qs("#cargos_page_info");
    const prev = qs("#cargos_prev");
    const next = qs("#cargos_next");

    const from = total ? (state.offset + 1) : 0;
    const to = Math.min(state.offset + state.limit, total);

    if (info) info.textContent = `${from}-${to} / ${total}`;

    if (prev) prev.disabled = state.offset <= 0;
    if (next) next.disabled = !has_more;
  }

  async function load() {
    setLoader(true);
    try {
      const r = await fetch(API_URL + buildQuery(), { credentials: "same-origin" });
      const j = await r.json();
      renderRows(j.results || []);
      renderPager(j.total || 0, !!j.has_more);
    } catch (e) {
      console.error("cargos load error", e);
    } finally {
      setLoader(false);
    }
  }

  function bind() {
    const search = qs("#cargo_search");
    if (search) {
      let t = null;
      search.addEventListener("input", () => {
        clearTimeout(t);
        t = setTimeout(() => {
          state.search = (search.value || "").trim();
          state.offset = 0;
          load();
        }, 250);
      });
    }

    const prev = qs("#cargos_prev");
    const next = qs("#cargos_next");
    if (prev) prev.addEventListener("click", () => {
      state.offset = Math.max(0, state.offset - state.limit);
      load();
    });
    if (next) next.addEventListener("click", () => {
      state.offset = state.offset + state.limit;
      load();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderHead();
    bind();
    load();
  });
})();
