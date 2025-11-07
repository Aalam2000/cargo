// ===============================
//  Cargo №1 — Главная страница
//  home.js (версия 2025.11)
//  ===============================
//
//  Функции:
//   1. Переключение вкладок (В пути / Доставленные / Оплаты)
//   2. Поиск и фильтрация данных
//   3. Получение и отображение суммы оплат клиента
//   4. Авто-показ баланса при входе клиента
//
// ===============================================

// -------------------------------
//  Переключение вкладок
// -------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      contents.forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    });
  });
});

// -------------------------------
//  Поиск по таблице (кнопка "Поиск")
// -------------------------------
function applyTableFilter(tab) {
  const clientInput = document.getElementById(`clientFilter_${tab}`);
  const productInput = document.getElementById(`productFilter_${tab}`);
  const clientCode = clientInput ? clientInput.value.trim() : "";
  const productCode = productInput ? productInput.value.trim() : "";

  const url = `/home/data/?tab=${tab}&client_code=${encodeURIComponent(clientCode)}&product_code=${encodeURIComponent(productCode)}`;

  fetch(url)
    .then((res) => res.json())
    .then((data) => renderTable(tab, data.results))
    .catch((err) => console.error("Ошибка фильтрации:", err));
}

// -------------------------------
//  Отрисовка таблицы
// -------------------------------
function renderTable(tab, rows) {
  const tbody = document.getElementById(`tbody_${tab}`);
  if (!tbody) return;
  tbody.innerHTML = "";

  if (!rows || rows.length === 0) {
    const cols = tab === "payments" ? 5 : 7;
    tbody.innerHTML = `<tr><td colspan="${cols}">Нет данных</td></tr>`;
    return;
  }

  const columns = Object.keys(rows[0]);
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((c) => {
      const td = document.createElement("td");
      td.textContent = row[c] ?? "";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

// -------------------------------
//  Живой фильтр (автообновление при вводе)
// -------------------------------
function debounce(func, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => func(...args), delay);
  };
}

document.addEventListener("DOMContentLoaded", () => {
  const filters = document.querySelectorAll(".input-filter");
  filters.forEach((input) => {
    input.addEventListener(
      "input",
      debounce(() => {
        const tab = input.closest(".tab-content").id.replace("tab-", "");
        liveFilter(tab);
      }, 300)
    );
  });
});

async function liveFilter(tab) {
  const params = new URLSearchParams({ tab });
  const productInput = document.getElementById(`productFilter_${tab}`);
  const clientInput = document.getElementById(`clientFilter_${tab}`);

  if (productInput?.value.trim()) params.append("product_code", productInput.value.trim());
  if (clientInput?.value.trim()) params.append("client_code", clientInput.value.trim());

  try {
    const res = await fetch(`/home/data/?${params.toString()}`);
    if (!res.ok) throw new Error("Ошибка сети");

    const data = await res.json();
    renderTable(tab, data.results);
  } catch (err) {
    console.error("Ошибка фильтрации:", err);
  }
}

// -------------------------------
//  Получение и отображение баланса клиента
// -------------------------------
async function updateClientBalance(clientCode = "") {
  const balanceBox = document.getElementById("client-balance");
  const valueElem = document.getElementById("balance-value");

  // если кода нет — скрываем блок
  if (!clientCode.trim()) {
    balanceBox.classList.add("hidden");
    valueElem.textContent = "—";
    return;
  }

  try {
    const res = await fetch(`/home/balance/?client_code=${encodeURIComponent(clientCode.trim())}`);
    if (!res.ok) throw new Error("Ошибка запроса");
    const data = await res.json();

    const paid = parseFloat(data.total_paid || 0);
    valueElem.textContent = `${paid.toLocaleString("ru-RU", { minimumFractionDigits: 2 })} AZN`;
    balanceBox.classList.remove("hidden");
  } catch (err) {
    console.error("Ошибка получения баланса клиента:", err);
    balanceBox.classList.add("hidden");
  }
}

// -------------------------------
//  Получение и отображение баланса клиента
// -------------------------------
async function updateClientBalance(clientCode = "") {
  const balanceBox = document.getElementById("client-balance");
  const valueElem = document.getElementById("balance-value");

  if (!clientCode.trim()) {
    balanceBox.classList.add("hidden");
    valueElem.textContent = "—";
    return;
  }

  try {
    const res = await fetch(`/home/balance/?client_code=${encodeURIComponent(clientCode.trim())}`);
    if (!res.ok) throw new Error("Ошибка запроса");
    const data = await res.json();

    const paid = parseFloat(data.total_paid || 0);
    const lastDate = data.last_payment_date || "";
    const lastAmount = parseFloat(data.last_payment_amount || 0);

    let text = `${paid.toLocaleString("ru-RU", { minimumFractionDigits: 2 })} AZN`;
    if (lastDate) {
      text += ` — Последний платеж ${lastDate} на ${lastAmount.toLocaleString("ru-RU", { minimumFractionDigits: 2 })} AZN`;
    }

    valueElem.textContent = text;
    balanceBox.classList.remove("hidden");
  } catch (err) {
    console.error("Ошибка получения баланса клиента:", err);
    balanceBox.classList.add("hidden");
  }
}

// -------------------------------
//  Автоматический показ баланса при входе клиента
// -------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  const roleMeta = document.querySelector('meta[name="user-role"]');
  const role = roleMeta ? roleMeta.content : "";

  if (role === "Client") {
    const balanceBox = document.getElementById("client-balance");
    const valueElem = document.getElementById("balance-value");

    try {
      const res = await fetch("/home/balance/");
      if (!res.ok) throw new Error("Ошибка запроса");
      const data = await res.json();

      const paid = parseFloat(data.total_paid || 0);
      const lastDate = data.last_payment_date || "";
      const lastAmount = parseFloat(data.last_payment_amount || 0);

      let text = `${paid.toLocaleString("ru-RU", { minimumFractionDigits: 2 })} AZN`;
      if (lastDate) {
        text += ` — Последний платеж ${lastDate} на ${lastAmount.toLocaleString("ru-RU", { minimumFractionDigits: 2 })} AZN`;
      }

      valueElem.textContent = text;
      balanceBox.classList.remove("hidden");
    } catch (err) {
      console.error("Ошибка автозагрузки баланса клиента:", err);
    }
  }
});

// ====================
//  Модальное окно добавления оплаты
// ====================
document.addEventListener("DOMContentLoaded", () => {
  const addBtn = document.getElementById("btnAddPayment");
  if (!addBtn) return;

  addBtn.addEventListener("click", openPaymentModal);
});

async function openPaymentModal(mode = "add", data = null) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay show";
  const modal = document.createElement("div");
  modal.className = "modal show";

  const headerText = mode === "edit" ? "Редактировать оплату" : "Добавить оплату";
  const payment = data || {};

  modal.innerHTML = `
    <div class="modal-header">${headerText}</div>
    <div class="modal-body">
      <label>Код клиента</label>
      <div style="position:relative">
        <input id="payClient" type="text" placeholder="Начните вводить..." value="${payment.client_code || ""}" />
        <div id="clientDropdown" class="dropdown-menu" style="display:none;position:absolute;top:42px;left:0;width:100%;z-index:1051"></div>
      </div>

      <label>Дата платежа</label>
      <input id="payDate" type="date" value="${payment.payment_date || new Date().toISOString().split('T')[0]}" disabled>

      <label>Сумма платежа</label>
      <input id="payAmount" type="number" step="0.01" value="${payment.amount_total || ""}" disabled>

      <label>Валюта</label>
      <select id="payCurrency" disabled>
        <option ${payment.currency==="RUB"?"selected":""}>RUB</option>
        <option ${payment.currency==="USD"?"selected":""}>USD</option>
        <option ${payment.currency==="EUR"?"selected":""}>EUR</option>
        <option ${payment.currency==="AZN"?"selected":""}>AZN</option>
      </select>

      <label>Курс</label>
      <input id="payRate" type="number" step="0.0001" value="${payment.exchange_rate || ""}" disabled>

      <label>Метод</label>
      <select id="payMethod" disabled>
        <option ${payment.method==="Наличные"?"selected":""}>Наличные</option>
        <option ${payment.method==="Банк"?"selected":""}>Банк</option>
        <option ${payment.method==="Счёт"?"selected":""}>Счёт</option>
      </select>

      <label>Комментарий</label>
      <textarea id="payComment" disabled>${payment.comment || ""}</textarea>
    </div>

    <div class="modal-footer">
      <button class="btn-cancel">Отмена</button>
      <button class="btn-save">Сохранить</button>
    </div>
  `;

  document.body.appendChild(overlay);
  document.body.appendChild(modal);

  const cancelBtn = modal.querySelector(".btn-cancel");
  const saveBtn = modal.querySelector(".btn-save");
  const clientInput = modal.querySelector("#payClient");
  const dropdown = modal.querySelector("#clientDropdown");
  const otherFields = modal.querySelectorAll("#payDate,#payAmount,#payCurrency,#payRate,#payMethod,#payComment");

  cancelBtn.onclick = () => { modal.remove(); overlay.remove(); };

  // === Автоподбор клиента ===
  clientInput.addEventListener("input", debounce(async () => {
    const search = clientInput.value.trim();
    if (!search) { dropdown.style.display = "none"; return; }
    const res = await fetch(`/api/get_clients/?search=${encodeURIComponent(search)}`);
    const data = await res.json();
    dropdown.innerHTML = "";
    (data.results || []).slice(0,7).forEach(c => {
      const div = document.createElement("div");
      div.className = "dropdown-item";
      div.textContent = c.client_code;
      div.onclick = () => {
        clientInput.value = c.client_code;
        dropdown.style.display = "none";
        otherFields.forEach(f => f.disabled = false);
      };
      dropdown.appendChild(div);
    });
    dropdown.style.display = data.results?.length ? "block" : "none";
  }, 300));

  saveBtn.onclick = async () => {
    const payload = {
      client_code: document.getElementById("payClient").value.trim(),
      payment_date: document.getElementById("payDate").value,
      amount_total: parseFloat(document.getElementById("payAmount").value),
      currency: document.getElementById("payCurrency").value,
      exchange_rate: parseFloat(document.getElementById("payRate").value) || 1,
      method: document.getElementById("payMethod").value,
      comment: document.getElementById("payComment").value.trim(),
      id: payment.id || null
    };

    const res = await fetch("/api/add_payment/", {
      method: mode === "edit" ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const resp = await res.json();

    if (resp.ok) {
      modal.remove();
      overlay.remove();
      applyTableFilter("payments");
    } else {
      alert("Ошибка: " + (resp.error || JSON.stringify(resp)));
    }
  };
}

// === Открытие модалки при клике по строке таблицы оплат ===
document.addEventListener("DOMContentLoaded", () => {
  const payTable = document.getElementById("tbody_payments");
  if (payTable) {
    payTable.addEventListener("click", (e) => {
      const tr = e.target.closest("tr");
      if (!tr || tr.children.length < 5) return;
      const paymentData = {
        id: tr.dataset.id,
        payment_date: tr.children[0].textContent.trim(),
        client_code: tr.children[1].textContent.trim(),
        amount_total: tr.children[2].textContent.trim(),
        method: tr.children[3].textContent.trim(),
        comment: tr.children[4].textContent.trim(),
      };
      openPaymentModal("edit", paymentData);
    });
  }
});
