// ==========================================================================
//   Cargo №1 — Главная страница
//   ПОЛНАЯ НОВАЯ ВЕРСИЯ home.js   (для полной замены)
//   Работает через новый API: /api/products_table/
// ==========================================================================

// ----------------------------
// Глобальное состояние
// ----------------------------
let ROLE = "";

// lazy pagination
const lazyState = {
    in_transit: {last_id: null, loading: false, finished: false},
    delivered: {last_id: null, loading: false, finished: false},
    payments: {last_id: null, loading: false, finished: false}
};

// ----------------------------
function debounce(fn, delay = 300) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), delay);
    };
}

// ----------------------------
async function getUserRole() {
    try {
        const res = await fetch("/api/user_role/");
        const data = await res.json();
        return data.role || "Unknown";
    } catch {
        return "Unknown";
    }
}

// ===============================
//  Баланс клиента (НОВАЯ ВЕРСИЯ)
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
        const res = await fetch(`/api/client_balance/?client_code=${encodeURIComponent(clientCode)}`);
        const data = await res.json();

        const paid = parseFloat(data.total_paid || 0);
        const lastDate = data.last_payment_date || "";
        const lastAmount = parseFloat(data.last_payment_amount || 0);

        let text = `${paid.toLocaleString("ru-RU", {minimumFractionDigits: 2})} AZN`;
        if (lastDate)
            text += ` — Последний платёж ${lastDate} на ${lastAmount.toLocaleString("ru-RU", {minimumFractionDigits: 2})} AZN`;

        val.textContent = text;
        box.classList.remove("hidden");

    } catch (err) {
        console.error("Ошибка получения баланса клиента:", err);
        box.classList.add("hidden");
    }
}

// автоматическая загрузка при входе клиента
async function updateClientBalanceAuto() {
    const box = document.getElementById("client-balance");
    const val = document.getElementById("balance-value");

    try {
        const res = await fetch("/api/client_balance/");
        const data = await res.json();

        const paid = parseFloat(data.total_paid || 0);
        const lastDate = data.last_payment_date || "";
        const lastAmount = parseFloat(data.last_payment_amount || 0);

        let text = `${paid.toLocaleString("ru-RU", {minimumFractionDigits: 2})} AZN`;
        if (lastDate)
            text += ` — Последний платёж ${lastDate} на ${lastAmount.toLocaleString("ru-RU", {minimumFractionDigits: 2})} AZN`;

        val.textContent = text;
        box.classList.remove("hidden");

    } catch (err) {
        console.error("Ошибка автозагрузки баланса:", err);
    }
}


// ==========================================================================
//     ЗАПРОС К ТОВАРАМ
// ==========================================================================
async function fetchProducts({tab, offset = 0, client = "", product = ""}) {
    const url = new URL("/api/products_table/", window.location.origin);
    url.searchParams.set("offset", offset);

    url.searchParams.set("tab", tab);
    url.searchParams.set("limit", "50");

    if (client) url.searchParams.set("filter[client__client_code]", client);
    if (product) url.searchParams.set("filter[product_code]", product);

    // поля — ФРОНТ просит только нужные
    // для таблицы нужны ВСЕ столбцы
    const fields = [
        "id", "product_code", "cargo_description", "client", "company",
        "warehouse", "cargo_type", "cargo_status", "packaging_type",
        "record_date", "departure_place", "destination_place",
        "weight", "volume", "cost", "insurance", "delivery_time",
        "shipping_date", "delivery_date", "comment",
        "qr_code", "qr_created_at"
    ];
    url.searchParams.set("fields", fields.join(","));

    const res = await fetch(url);
    return await res.json();
}

// ==========================================================================
//     ПОСТРОЕНИЕ ШАПКИ ТАБЛИЦЫ (динамическое)
// ==========================================================================
function buildTableHeader(tab, columns) {
    const table = document.getElementById(`table_${tab}`);
    if (!table) return;

    let html = "<thead><tr>";

    for (const col of columns) {
        html += `<th data-field="${col}">${col}</th>`;
    }
    html += "</tr></thead><tbody id='tbody_" + tab + "'></tbody>";

    table.innerHTML = html;
}

// ==========================================================================
//     ОТРИСОВКА СТРОК
// ==========================================================================
function appendRows(tab, rows) {
    const tbody = document.getElementById(`tbody_${tab}`);
    if (!tbody) return;

    rows.forEach((row) => {
        const tr = document.createElement("tr");

        tr.innerHTML = Object.values(row)
            .map(v => `<td>${v ?? ""}</td>`)
            .join("");

        tbody.appendChild(tr);
    });
}

// ==========================================================================
//     L A Z Y   P A G I N A T I O N
// ==========================================================================
function resetLazy(tab) {
    const st = lazyState[tab];
    st.loading = false;
    st.finished = false;

    const tbody = document.getElementById(`tbody_${tab}`);
    if (tbody) tbody.innerHTML = "";
}

async function loadMore(tab, clear = false) {
    const st = lazyState[tab];
    if (st.loading || st.finished) return;
    st.loading = true;
    // вкладка "Оплаты" не использует API товаров
    if (tab === "payments") {
        try {
            const offset = document.getElementById("tbody_payments").children.length;
            const data = await fetchPayments({offset});

            if (!data.results || data.results.length === 0) {
                st.finished = true;
                return;
            }

            // строим шапку один раз
            if (!st.last_id) {
                const first = data.results[0];
                buildPaymentsHeader(Object.keys(first));
            }

            appendPaymentRows(data.results);
            initPaymentsClicks();

            if (!data.has_more) st.finished = true;

        } catch (err) {
            console.error("Ошибка загрузки платежей:", err);
        }
        st.loading = false;
        return;
    }

    const offset = document
        .getElementById(`tbody_${tab}`)
        ?.children.length || 0;

    const client = document.getElementById("clientFilter")?.value || "";
    const productInput = document.getElementById(`productFilter_${tab}`);
    const product = productInput ? productInput.value : "";

    try {
        const data = await fetchProducts({
            tab,
            offset,
            client: client.trim(),
            product: product.trim()
        });

        if (!data.results || data.results.length === 0) {
            st.finished = true;
            return;
        }

        // если это первая загрузка → строим шапку
        if (!st.last_id) {
            const first = data.results[0];
            buildTableHeader(tab, Object.keys(first));
        }

        appendRows(tab, data.results);

        if (!data.has_more) st.finished = true;

    } catch (err) {
        console.error("Ошибка загрузки:", err);
    }

    st.loading = false;
}

// ==========================================================================
//     БЛОК ОПЛАТ
// ==========================================================================
async function fetchPayments({offset = 0}) {
    const url = new URL("/api/payments_table/", window.location.origin);

    url.searchParams.set("offset", offset);
    url.searchParams.set("limit", "50");

    // сортировка
    if (window.paySortBy) url.searchParams.set("sort_by", window.paySortBy);
    if (window.paySortDir) url.searchParams.set("sort_dir", window.paySortDir);

    // фильтр клиента (общий)
    const cf = document.getElementById("clientFilter")?.value || "";
    if (cf) url.searchParams.set("client_code", cf.trim());

    return await fetch(url).then(r => r.json());
}

function buildPaymentsHeader(columns) {
    const table = document.querySelector("#tab-payments table");
    let html = "<thead><tr>";

    columns.forEach(col => {
        html += `<th data-field="${col}" class="sortable">${col}</th>`;
    });

    html += "</tr></thead><tbody id='tbody_payments'></tbody>";
    table.innerHTML = html;

    // клики на сортировку
    table.querySelectorAll("th.sortable").forEach(th => {
        th.addEventListener("click", () => {
            const f = th.dataset.field;
            if (window.paySortBy === f) {
                window.paySortDir = window.paySortDir === "asc" ? "desc" : "asc";
            } else {
                window.paySortBy = f;
                window.paySortDir = "asc";
            }
            resetLazy("payments");
            loadMore("payments");
        });
    });
}

function appendPaymentRows(rows) {
    const tbody = document.getElementById("tbody_payments");
    rows.forEach(row => {
        const tr = document.createElement("tr");
        tr.dataset.id = row.id || row._id;
        tr.innerHTML = Object.keys(row)
            .filter(k => !["_id","id"].includes(k))
            .map(k => `<td>${row[k] ?? ""}</td>`)
            .join("");
        tbody.appendChild(tr);
    });
}


// ==========================================================================
//     ФИЛЬТРЫ
// ==========================================================================
function applyTableFilter(tab) {
    resetLazy(tab);
    loadMore(tab);
}

// ==========================================================================
//     ОПЛАТЫ — ЛОГИКА СОХРАНЕНА 1-в-1
// ==========================================================================
function initPaymentsClicks() {
    const payTable = document.getElementById("tbody_payments");
    if (!payTable) return;

    if (ROLE === "Admin" || ROLE === "Operator") {
        payTable.addEventListener("click", async e => {
            const tr = e.target.closest("tr");
            if (!tr) return;

            const payId = tr.dataset.id;
            if (!payId) return;

            try {
                const res = await fetch(`/api/add_payment/?id=${payId}`);
                const data = await res.json();
                openPaymentModal("edit", data);
            } catch (err) {
                console.error("Ошибка загрузки платежа:", err);
            }
        });
    }
}

/* =====================================================
       МОДАЛКА ОПЛАТ — ПОЛНАЯ ВЕРСИЯ (ВАРИАНТ B)
   ===================================================== */

async function openPaymentModal(mode = "add", data = null) {
    const p = data || {};
    const headerText = mode === "edit" ? "Редактирование оплаты" : "Новая оплата";

    const html = `
    <div class="modal">
        <div class="modal-header">${headerText}</div>
        <div class="modal-body">

            <div class="modal-row select-search-wrapper">
                <label>Код клиента</label>
                <input id="payClient" type="text" autocomplete="off"
                       placeholder="Введите код клиента..."
                       class="select-search-input"
                       value="${p.client_code || ""}"
                       ${mode === "edit" ? "disabled" : ""}>
            </div>

            <div class="modal-row">
                <label>Дата платежа</label>
                <input id="payDate" type="date"
                       value="${p.payment_date || new Date().toISOString().split("T")[0]}">
            </div>

            <div class="modal-row">
                <label>Сумма платежа</label>
                <input id="payAmount" type="number" step="0.01"
                       value="${p.amount_total || ""}">
            </div>

            <div class="modal-row">
                <label>Валюта</label>
                <select id="payCurrency">
                    <option ${p.currency === "AZN" ? "selected" : ""}>AZN</option>
                    <option ${p.currency === "USD" ? "selected" : ""}>USD</option>
                    <option ${p.currency === "EUR" ? "selected" : ""}>EUR</option>
                    <option ${p.currency === "RUB" ? "selected" : ""}>RUB</option>
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
                <select id="payMethod">
                    <option value="cash" ${p.method === "cash" ? "selected" : ""}>Наличные</option>
                    <option value="bank" ${p.method === "bank" ? "selected" : ""}>Безнал</option>
                    <option value="pos" ${p.method === "pos" ? "selected" : ""}>POS</option>
                    <option value="offset" ${p.method === "offset" ? "selected" : ""}>Взаимозачёт</option>
                </select>
            </div>

            <div class="modal-row">
                <label>Комментарий</label>
                <textarea id="payComment">${p.comment || ""}</textarea>
            </div>

        </div>

        <div class="modal-footer">
            <button class="btn-save">Сохранить</button>
            <button class="btn-cancel">Отмена</button>
        </div>
    </div>`;

    const inst = openModal({ html, modalName: "payment", closable: true });
    const modal = inst.modal;

    /* ===========================
            Автопоиск клиента
       =========================== */

    const input = modal.querySelector("#payClient");
    let dropdown = modal.querySelector(".client-autocomplete");
    if (!dropdown) {
        dropdown = document.createElement("div");
        dropdown.className = "client-autocomplete autocomplete-list hidden";
        input.parentElement.appendChild(dropdown);
    }
    let clientsCache = [];

    async function loadClients() {
        if (clientsCache.length) return clientsCache;
        const r = await fetch("/api/get_clients/?page_size=99999");
        const j = await r.json();
        clientsCache = j.results || j;   // поддерживаем оба формата
        return clientsCache;
    }

    async function showDropdown() {
        if (input.disabled) return;
        const q = input.value.trim().toLowerCase();
        const list = await loadClients();
        const filtered = q
            ? list.filter(c => c.client_code.toLowerCase().includes(q))
            : list.slice(0, 7);

        if (!filtered.length) {
            dropdown.innerHTML = `<div class="autocomplete-empty">Нет совпадений</div>`;
        } else {
            dropdown.innerHTML = filtered
                .map(c => `<div class="autocomplete-item">${c.client_code}</div>`)
                .join("");
        }

        dropdown.style.position = "absolute";
        dropdown.style.top = (input.offsetTop + input.offsetHeight) + "px";
        dropdown.style.left = input.offsetLeft + "px";
        dropdown.style.width = input.offsetWidth + "px";


        dropdown.classList.remove("hidden");

        dropdown.querySelectorAll(".autocomplete-item").forEach(item => {
            item.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                input.value = item.textContent.trim();
                dropdown.classList.add("hidden");
                dropdown.innerHTML = "";
            };



        });
    }

    input.addEventListener("input", showDropdown);
    input.addEventListener("focus", () => {
        if (dropdown.innerHTML.trim() !== "") dropdown.classList.remove("hidden");
    });


    document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target) && e.target !== input) {
            dropdown.classList.add("hidden");
        }
    });



    /* ===========================
           Пересчёт USD
       =========================== */

    function recalcUSD() {
        const amt = parseFloat(document.getElementById("payAmount").value) || 0;
        const rate = parseFloat(document.getElementById("payRate").value) || 1;
        document.getElementById("payUSD").value = (amt / rate).toFixed(2);
    }

    async function fetchExchangeRate() {
        const cur = document.getElementById("payCurrency").value;
        const date = document.getElementById("payDate").value;
        const rateEl = document.getElementById("payRate");
        if (!cur) return;

        if (cur === "USD") {
            rateEl.value = 1;
            recalcUSD();
            return;
        }

        try {
            let r = await fetch(`/api/get_rate/?currency=${cur}&date=${date}`);
            let d = await r.json();

            if (!r.ok || !d.rate) {
                // пробуем текущую дату
                const today = new Date().toISOString().split("T")[0];
                r = await fetch(`/api/get_rate/?currency=${cur}&date=${today}`);
                d = await r.json();
            }

            if (!d.rate) {
                document.getElementById("payRate").value = 1;
                recalcUSD();
                return;
            }

            rateEl.value = d.rate;
            recalcUSD();

            rateEl.value = d.rate || 1;
            recalcUSD();
        } catch (e) {
            console.error("rate error", e);
        }
    }

    modal.querySelector(".btn-cancel").onclick = () => inst.close();

    modal.querySelector(".btn-save").onclick = async () => {
        const payload = {
            id: p.id || null,
            client_code: document.getElementById("payClient").value.trim(),
            payment_date: document.getElementById("payDate").value,
            amount_total: parseFloat(document.getElementById("payAmount").value) || 0,
            currency: document.getElementById("payCurrency").value,
            exchange_rate: parseFloat(document.getElementById("payRate").value) || 1,
            method: document.getElementById("payMethod").value,
            comment: document.getElementById("payComment").value.trim(),
        };

        const res = await fetch("/api/add_payment/", {
            method: mode === "edit" ? "PUT" : "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": window.getCsrf()
            },
            body: JSON.stringify(payload)
        });

        const txt = await res.text();
        if (!res.ok) return alert("Ошибка: " + txt);

        inst.close();
        resetLazy("payments");
        loadMore("payments");
    };

    document.getElementById("payCurrency").addEventListener("change", fetchExchangeRate);
    document.getElementById("payDate").addEventListener("change", fetchExchangeRate);
    document.getElementById("payAmount").addEventListener("input", recalcUSD);
    document.getElementById("payRate").addEventListener("input", recalcUSD);

    if (mode === "add") fetchExchangeRate();
}

/* =====================================================
          Клик по строкам оплаты → открыть edit
   ===================================================== */

function initPaymentsClicks() {
    const payTable = document.getElementById("tbody_payments");
    if (!payTable) return;

    if (ROLE === "Admin" || ROLE === "Operator") {
        payTable.addEventListener("click", async (e) => {
            const tr = e.target.closest("tr");
            if (!tr) return;

            const id = tr.dataset.id;
            if (!id) return;

            const r = await fetch(`/api/add_payment/?id=${id}`);
            const d = await r.json();
            openPaymentModal("edit", d);
        });
    }
}


// ==========================================================================
//     СТАРТ
// ==========================================================================
document.addEventListener("DOMContentLoaded", async () => {

    ROLE = await getUserRole();
    const addBtn = document.getElementById("btnAddPayment");
    if (addBtn && (ROLE === "Admin" || ROLE === "Operator")) {
        addBtn.addEventListener("click", () => openPaymentModal("add"));
    }
    // вкладки
    const tabs = document.querySelectorAll(".tab-btn");
    const contents = document.querySelectorAll(".tab-content");

    tabs.forEach((btn) => {
        btn.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            contents.forEach(c => c.classList.remove("active"));
            btn.classList.add("active");

            const tab = btn.dataset.tab;
            document.getElementById("tab-" + tab).classList.add("active");

            resetLazy(tab);
            loadMore(tab);
        });
    });

    // live filter
    document.querySelectorAll(".input-filter").forEach((input) => {
        input.addEventListener(
            "input",
            debounce(() => {

                // ========================
                // 1) ФИЛЬТР ПО КЛИЕНТУ
                // ========================
                if (input.id === "clientFilter") {
                    ["in_transit", "delivered"].forEach(tab => {
                        resetLazy(tab);
                        loadMore(tab);
                    });
                    return;
                }

                // ============================
                // 2) ФИЛЬТРЫ ПО НОМЕРУ ТОВАРА
                //    (внутри вкладок)
                // ============================
                const tabBlock = input.closest(".tab-content");
                if (!tabBlock) return;

                const tab = tabBlock.id.replace("tab-", "");
                resetLazy(tab);
                loadMore(tab);

            }, 300)
        );
    });


    // scroll lazy
    document.querySelectorAll(".table-wrapper").forEach((wr) => {
        const tab = wr.dataset.tab;
        wr.addEventListener("scroll", () => {
            if (wr.scrollTop + wr.clientHeight >= wr.scrollHeight - 200) {
                loadMore(tab);
            }
        });
    });

    // первая загрузка
    resetLazy("in_transit");
    loadMore("in_transit");

    initPaymentsClicks();
    if (ROLE === "Client") {
        updateClientBalanceAuto();
    }

});
