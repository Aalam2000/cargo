let offset = 0;
const limit = 50;
let loading = false;
let hasMore = true;
let filters = {};
let userConfig = null;

async function fetchUserConfig() {
  const res = await fetch("/api/cargo_table/config/");
  if (!res.ok) return null;
  return await res.json();
}

async function fetchCargoData(reset = false) {
  if (loading || !hasMore) return;
  loading = true;
  document.getElementById("loader").style.display = "block";

  const params = new URLSearchParams({ offset, limit, ...filters });
  const res = await fetch(`/api/cargo_table/data/?${params.toString()}`);
  const json = await res.json();

  if (reset) {
    document.getElementById("cargo-body").innerHTML = "";
    offset = 0;
  }

  renderRows(json.results || []);
  offset += json.results.length;
  hasMore = json.has_more;
  loading = false;
  document.getElementById("loader").style.display = hasMore ? "block" : "none";
}

function renderHeader(columns) {
  const headerRow = document.getElementById("cargo-header-row");
  headerRow.innerHTML = "";
  columns.forEach(col => {
    if (!col.visible) return;
    const th = document.createElement("th");
    th.textContent = col.label;
    headerRow.appendChild(th);
  });
}

function renderRows(rows) {
  const tbody = document.getElementById("cargo-body");
  const frag = document.createDocumentFragment();

  rows.forEach(row => {
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

function setupFilters() {
  document.querySelectorAll(".filter-container input").forEach(inp => {
    inp.addEventListener("input", () => {
      filters[inp.id.replace("filter-", "")] = inp.value;
      offset = 0;
      hasMore = true;
      fetchCargoData(true);
    });
  });
}

window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
    fetchCargoData();
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  userConfig = await fetchUserConfig();
  if (!userConfig || !userConfig.columns) return;
  renderHeader(userConfig.columns);
  setupFilters();
  fetchCargoData();
});
