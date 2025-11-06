// web/static/js/home.js

// ======== Переключение вкладок ========
document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      contents.forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    });
  });
});

// ======== Обычный поиск (кнопка "Поиск") ========
function applyTableFilter(tab) {
  const params = new URLSearchParams();

  if (tab === "in_transit" || tab === "delivered") {
    const productInput = document.getElementById(`productFilter_${tab}`);
    const clientSelect = document.getElementById(`clientFilter_${tab}`);
    if (productInput && productInput.value.trim()) {
      params.append("product_code", productInput.value.trim());
    }
    if (clientSelect && clientSelect.value) {
      params.append("client_id", clientSelect.value);
    }
  }

  if (tab === "payments") {
    const clientSelect = document.getElementById("clientFilter_payments");
    if (clientSelect && clientSelect.value) {
      params.append("client_id", clientSelect.value);
    }
  }

  // переход по ссылке /home/ с параметрами
  window.location.href = "/home/?" + params.toString();
}

// ======== LIVE FILTER (мгновенная фильтрация без reload) ========

// Отложенный вызов (debounce)
function debounce(func, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => func(...args), delay);
  };
}

document.addEventListener("DOMContentLoaded", () => {
  const filters = document.querySelectorAll(".input-filter");
  filters.forEach(el => {
    el.addEventListener(
      "input",
      debounce(() => {
        const tab = el.closest(".tab-content").id.replace("tab-", "");
        liveFilter(tab);
      }, 300)
    );
  });
});

// Основная функция живого фильтра
async function liveFilter(tab) {
  const params = new URLSearchParams({ tab });

  const productInput = document.getElementById(`productFilter_${tab}`);
  const clientSelect = document.getElementById(`clientFilter_${tab}`);

  if (productInput?.value.trim()) params.append("product_code", productInput.value.trim());
  if (clientSelect?.value.trim()) params.append("client_code", clientSelect.value.trim());

  try {
    const response = await fetch(`/home/data/?${params.toString()}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });
    if (!response.ok) throw new Error("Ошибка сети");

    const data = await response.json();
    const tbody = document.getElementById(`tbody_${tab}`);
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!data.results?.length) {
      const cols = tab === "payments" ? 5 : 7;
      tbody.innerHTML = `<tr><td colspan="${cols}">Нет данных</td></tr>`;
      return;
    }

    for (const row of data.results) {
      const tr = document.createElement("tr");
      tr.innerHTML = Object.values(row)
        .map(v => `<td>${v ?? ""}</td>`)
        .join("");
      tbody.appendChild(tr);
    }
  } catch (err) {
    console.error("Ошибка фильтрации:", err);
  }
}
