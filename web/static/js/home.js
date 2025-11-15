// ===============================
//  Cargo №1 — Главная страница
//  home.js (версия 2025.11, исправленная)
// ===============================

// --- Глобальные переменные ---
let ROLE = "";

// --- Получение роли пользователя ---
async function getUserRole() {
    try {
        const res = await fetch("/api/user_role/");
        if (!res.ok) throw new Error("Ошибка получения роли");
        const data = await res.json();
        return data.role || "Unknown";
    } catch (err) {
        console.error("Ошибка getUserRole:", err);
        return "Unknown";
    }
}


document.addEventListener("DOMContentLoaded", async () => {
    // 1️⃣ Получаем роль перед основной инициализацией
    ROLE = await getUserRole();
    console.log("🎭 Текущая роль:", ROLE);
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

    // --- Живой фильтр ---
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

    // --- Кнопка добавления оплаты ---
    const addBtn = document.getElementById("btnAddPayment");
    if (addBtn && (ROLE === "Admin" || ROLE === "Operator")) {
        addBtn.addEventListener("click", () => openPaymentModal("add"));
    } else if (addBtn && ROLE === "Client") {
        addBtn.remove(); // клиенту не показываем кнопку
    }
    // --- Кликабельность строк таблицы оплат ---
    const payTable = document.getElementById("tbody_payments");

    if (payTable) {
        if (ROLE === "Admin" || ROLE === "Operator") {
            console.log(`🟩 payTable найден, клики включены для роли: ${ROLE}`);

            // Устанавливаем курсор "pointer" и назначаем обработчик
            payTable.querySelectorAll("tr").forEach((tr) => {
                tr.style.cursor = "pointer";
            });

            payTable.addEventListener("click", async (e) => {
                const tr = e.target.closest("tr");
                if (!tr) return;
                const payId = tr.dataset.id;
                if (!payId) return;

                try {
                    console.log(`📡 Загрузка данных платежа ID=${payId}`);
                    const res = await fetch(`/api/add_payment/?id=${payId}`);
                    const data = await res.json();

                    if (data.error) return alert(data.error);
                    if (data.payment_date?.includes("T"))
                        data.payment_date = data.payment_date.split("T")[0];

                    openPaymentModal("edit", data);
                } catch (err) {
                    console.error("💥 Ошибка загрузки платежа:", err);
                    alert("Не удалось загрузить данные платежа с сервера.");
                }
            });
        } else {
            // Для клиентов и неизвестных ролей — курсор обычный, без кликов
            console.log(`🚫 Клики по таблице отключены для роли: ${ROLE}`);
            payTable.querySelectorAll("tr").forEach((tr) => {
                tr.style.cursor = "default";
            });
        }
    } else {
        console.warn("⚠️ payTable (tbody_payments) не найден на странице");
    }

});

// ===============================
//  Поиск и фильтрация таблиц
// ===============================
function applyTableFilter(tab) {
    const clientInput = document.getElementById(`clientFilter_${tab}`);
    const productInput = document.getElementById(`productFilter_${tab}`);
    const url = `/home/data/?tab=${tab}&client_code=${encodeURIComponent(clientInput?.value.trim() || "")}&product_code=${encodeURIComponent(productInput?.value.trim() || "")}`;
    fetch(url)
        .then((r) => r.json())
        .then((data) => renderTable(tab, data.results))
        .catch((e) => console.error("Ошибка фильтрации:", e));
}

function renderTable(tab, rows) {
    const tbody = document.getElementById(`tbody_${tab}`);
    if (!tbody) return;
    tbody.innerHTML = "";
    if (!rows?.length) {
        const cols = tab === "payments" ? 5 : 7;
        tbody.innerHTML = `<tr><td colspan="${cols}">Нет данных</td></tr>`;
        return;
    }
    const columns = Object.keys(rows[0]);
    rows.forEach((r) => {
        const tr = document.createElement("tr");
        tr.dataset.id = r.id || "";
        columns.forEach((c) => {
            const td = document.createElement("td");
            td.textContent = r[c] ?? "";
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

function debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}

async function liveFilter(tab) {
    const params = new URLSearchParams({tab});
    const productInput = document.getElementById(`productFilter_${tab}`);
    const clientInput = document.getElementById(`clientFilter_${tab}`);
    if (productInput?.value.trim()) params.append("product_code", productInput.value.trim());
    if (clientInput?.value.trim()) params.append("client_code", clientInput.value.trim());
    try {
        const res = await fetch(`/home/data/?${params}`);
        const data = await res.json();
        renderTable(tab, data.results);
    } catch (err) {
        console.error("Ошибка фильтрации:", err);
    }
}

// ===============================
//  Баланс клиента
// ===============================
async function updateClientBalance(clientCode = "") {
    const box = document.getElementById("client-balance");
    const val = document.getElementById("balance-value");
    if (!clientCode.trim()) {
        box.classList.add("hidden");
        val.textContent = "—";
        return;
    }
    try {
        const res = await fetch(`/home/balance/?client_code=${encodeURIComponent(clientCode)}`);
        const data = await res.json();
        const paid = parseFloat(data.total_paid || 0);
        const lastDate = data.last_payment_date || "";
        const lastAmount = parseFloat(data.last_payment_amount || 0);
        let text = `${paid.toLocaleString("ru-RU", {minimumFractionDigits: 2})} AZN`;
        if (lastDate)
            text += ` — Последний платеж ${lastDate} на ${lastAmount.toLocaleString("ru-RU", {minimumFractionDigits: 2})} AZN`;
        val.textContent = text;
        box.classList.remove("hidden");
    } catch (err) {
        console.error("Ошибка получения баланса клиента:", err);
        box.classList.add("hidden");
    }
}

async function updateClientBalanceAuto() {
    try {
        const res = await fetch("/home/balance/");
        const data = await res.json();
        const paid = parseFloat(data.total_paid || 0);
        const lastDate = data.last_payment_date || "";
        const lastAmount = parseFloat(data.last_payment_amount || 0);
        let text = `${paid.toLocaleString("ru-RU", {minimumFractionDigits: 2})} AZN`;
        if (lastDate)
            text += ` — Последний платеж ${lastDate} на ${lastAmount.toLocaleString("ru-RU", {minimumFractionDigits: 2})} AZN`;
        document.getElementById("balance-value").textContent = text;
        document.getElementById("client-balance").classList.remove("hidden");
    } catch (err) {
        console.error("Ошибка автозагрузки баланса:", err);
    }
}

async function openPaymentModal(mode = "add", data = null) {
  const headerText = mode === "edit" ? "Редактировать оплату" : "Добавить оплату";
  const p = data || {};

  // --- HTML с обёртками .modal-row ---
  const html = `
  <div class="modal">
    <div class="modal-header">${headerText}</div>
    <div class="modal-body">
      <div class="modal-row">
        <label>Код клиента</label>
        <input id="payClient" type="text" placeholder="Начните вводить..." 
          value="${p.client_code || ""}" ${mode === "edit" ? "disabled" : ""}/>
      </div>

      <div class="modal-row">
        <label>Груз</label>
        <input id="payCargo" type="text" placeholder="Выберите груз" 
          value="${p.cargo_code || ""}" ${mode === "edit" ? "" : "disabled"}/>
      </div>

      <div class="modal-row">
        <label>Дата платежа</label>
        <input id="payDate" type="date" 
          value="${p.payment_date || new Date().toISOString().split("T")[0]}" 
          ${mode === "edit" ? "" : "disabled"}>
      </div>

      <div class="modal-row">
        <label>Сумма платежа</label>
        <input id="payAmount" type="number" step="0.01" 
          value="${p.amount_total || ""}" ${mode === "edit" ? "" : "disabled"}>
      </div>

      <div class="modal-row">
        <label>Валюта</label>
        <select id="payCurrency" ${mode === "edit" ? "" : "disabled"}>
          <option ${p.currency === "RUB" ? "selected" : ""}>RUB</option>
          <option ${p.currency === "USD" ? "selected" : ""}>USD</option>
          <option ${p.currency === "EUR" ? "selected" : ""}>EUR</option>
          <option ${p.currency === "AZN" ? "selected" : ""}>AZN</option>
        </select>
      </div>

      <div class="modal-row">
        <label>Курс к USD</label>
        <input id="payRate" type="number" step="0.0001" 
          value="${p.exchange_rate || ""}">
      </div>

      <div class="modal-row">
        <label>Сумма в USD</label>
        <input id="payUSD" type="number" step="0.01" readonly 
          value="${p.amount_usd || ""}">
      </div>

      <div class="modal-row">
        <label>Метод оплаты</label>
        <select id="payMethod" ${mode === "edit" ? "" : "disabled"}>
          <option value="cash" ${p.method === "cash" ? "selected" : ""}>Наличные</option>
          <option value="bank" ${p.method === "bank" ? "selected" : ""}>Безнал</option>
          <option value="pos" ${p.method === "pos" ? "selected" : ""}>POS-терминал</option>
          <option value="offset" ${p.method === "offset" ? "selected" : ""}>Взаимозачёт</option>
        </select>
      </div>

      <div class="modal-row">
        <label>Комментарий</label>
        <textarea id="payComment" ${mode === "edit" ? "" : "disabled"}>${p.comment || ""}</textarea>
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn-save">Сохранить</button>
      <button class="btn-cancel">Отмена</button>
    </div>
  </div>`;

  const inst = openModal({ html, modalName: 'payment', closable: true });
  const modal = inst.modal;

  // === Логика ===
  const recalcUSD = () => {
    const amt = parseFloat(document.getElementById("payAmount").value) || 0;
    const rate = parseFloat(document.getElementById("payRate").value) || 1;
    document.getElementById("payUSD").value = (amt / rate).toFixed(2);
  };

  async function fetchExchangeRate() {
    const cur = document.getElementById("payCurrency").value;
    const date = document.getElementById("payDate").value;
    const rateEl = document.getElementById("payRate");
    if (!cur || !date) return;
    if (cur === "USD") { rateEl.value = 1; recalcUSD(); return; }
    try {
      const resp = await fetch(`/api/get_rate/?currency=${cur}&date=${date}`);
      const data = await resp.json();
      if (data.rate) { rateEl.value = data.rate; recalcUSD(); }
    } catch (err) { console.error("Ошибка курса:", err); }
  }

  modal.querySelector(".btn-cancel").onclick = () => inst.close();
  modal.querySelector(".btn-save").onclick = async () => {
    const payload = {
      id: p.id || null,
      client_code: document.getElementById("payClient").value.trim(),
      cargo_code: document.getElementById("payCargo").value.trim(),
      payment_date: document.getElementById("payDate").value,
      amount_total: parseFloat(document.getElementById("payAmount").value) || 0,
      currency: document.getElementById("payCurrency").value,
      exchange_rate: parseFloat(document.getElementById("payRate").value) || 1,
      method: document.getElementById("payMethod").value,
      comment: document.getElementById("payComment").value.trim(),
    };

    const res = await fetch("/api/add_payment/", {
      method: mode === "edit" ? "PUT" : "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": window.getCsrf() },
      body: JSON.stringify(payload),
    });

    const text = await res.text();
    if (!res.ok) return alert("Ошибка: " + res.status + "\n" + text);
    const j = JSON.parse(text);
    if (j.ok) { inst.close(); applyTableFilter("payments"); }
    else alert("Ошибка: " + (j.error || JSON.stringify(j)));
  };

  document.getElementById("payCurrency").addEventListener("change", fetchExchangeRate);
  document.getElementById("payDate").addEventListener("change", fetchExchangeRate);
  document.getElementById("payAmount").addEventListener("input", recalcUSD);
  document.getElementById("payRate").addEventListener("input", recalcUSD);

  if (mode === "add") await fetchExchangeRate();
}
