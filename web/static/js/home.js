// ==========================================================================
//   Cargo №1 — Главная страница
//   ПОЛНАЯ НОВАЯ ВЕРСИЯ home.js   (для полной замены)
//   Работает через новый API: /api/products_table/
// ==========================================================================

// ----------------------------
// Глобальное состояние
// ----------------------------
let ROLE = "";

const PRODUCT_COLUMN_LABELS = {
    product_code: "Номер товара",
    client: "Код клиента",
    cargo: "Груз",
    cargo_status: "Статус",
    warehouse: "Склад",

    record_date: "Дата записи",
    shipping_date: "Дата отправки",
    delivery_date: "Дата доставки",

    cargo_description: "Описание груза",
    comment: "Комментарий",

    weight: "Вес",
    volume: "Объём",
    cost: "Стоимость",
    images: "Фото",
};


const PRODUCT_SORTABLE_FIELDS = new Set(["product_code", "client", "cargo", "warehouse"]);


// lazy pagination
const lazyState = {
    in_transit: {last_id: null, loading: false, finished: false, req: 0},
    delivered: {last_id: null, loading: false, finished: false, req: 0},
    payments: {last_id: null, loading: false, finished: false, req: 0}
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
    const info = document.getElementById("clientInfo");

    if (!clientCode.trim()) {
        box.classList.add("hidden");
        val.textContent = "—";
        if (info) info.textContent = "";
        return;
    }

    try {
        const res = await fetch(`/api/client_balance/?client_code=${encodeURIComponent(clientCode)}`);
        const data = await res.json();

        const balance = parseFloat(data.balance || 0);
        const status = balance >= 0 ? "Недоплата" : "Аванс";

        let text = `Баланс: ${status} ${Math.abs(balance).toLocaleString("ru-RU",{minimumFractionDigits:2})} USD`;

        if (data.last_payment_date)
            text += ` — последний платёж ${data.last_payment_date} на ${data.last_payment_amount} USD`;

        val.textContent = text;
        box.classList.remove("hidden");

        if (info && data.user_name)
            info.textContent = `${data.user_name} (${data.client_code})`;

    } catch (err) {
        console.error("Ошибка получения баланса клиента:", err);
    }
}

// автоматическая загрузка при входе клиента
async function updateClientBalanceAuto() {
    const box = document.getElementById("client-balance");
    const val = document.getElementById("balance-value");
    const info = document.getElementById("clientInfo");

    try {
        const res = await fetch("/api/client_balance/");
        const data = await res.json();

        const balance = parseFloat(data.balance || 0);
        const status = balance >= 0 ? "Недоплата" : "Аванс";

        let text = `Баланс: ${status} ${Math.abs(balance).toLocaleString("ru-RU",{minimumFractionDigits:2})} USD`;

        if (data.last_payment_date)
            text += ` — последний платёж ${data.last_payment_date} на ${data.last_payment_amount} USD`;

        val.textContent = text;
        box.classList.remove("hidden");

        if (info && data.user_name)
            info.textContent = `${data.user_name} (${data.client_code})`;

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
    if (window.prodSortBy) url.searchParams.set("sort_by", window.prodSortBy);
    if (window.prodSortDir) url.searchParams.set("sort_dir", window.prodSortDir);


    if (client) url.searchParams.set("filter[client]", client);
    if (product) url.searchParams.set("filter[product_code]", product);
    const cargoInput = document.getElementById(`productFilter_${tab}`);
    if (cargoInput && cargoInput.value.trim()) {
        url.searchParams.set("filter[cargo]", cargoInput.value.trim());
    }

    // поля — ФРОНТ просит только нужные
    let fields = [
        "id",
        "product_code",
        "record_date",
        "cargo_description",
        "comment",
        "shipping_date",
        "delivery_date",
        "client",
        "warehouse",
        "cargo_status"
    ];
    if (ROLE === "Client") {
        fields = fields.filter(f => f !== "client");
    }

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
        const label = PRODUCT_COLUMN_LABELS[col] || col;
        const sortable = PRODUCT_SORTABLE_FIELDS.has(col);

        html += sortable
            ? `<th data-field="${col}" class="sortable" style="cursor:pointer;">${label}</th>`
            : `<th>${label}</th>`;
    }

    html += "</tr></thead><tbody id='tbody_" + tab + "'></tbody>";

    table.innerHTML = html;
    table.querySelectorAll("th.sortable").forEach(th => {
        th.addEventListener("click", () => {
            const field = th.dataset.field;   // теперь сразу истинное поле
            window.prodSortBy = field;

            if (window.prodSortDir === "asc") {
                window.prodSortDir = "desc";
            } else {
                window.prodSortDir = "asc";
            }

            resetLazy(tab);
            loadMore(tab);

        });
    });

}

const PRODUCT_SORT_MAP = {
    "Код товара": "product_code",
    "Дата записи": "record_date",
    "Дата отправки": "shipping_date",
    "Дата доставки": "delivery_date",
    "Статус": "cargo_status",
    "Склад": "warehouse",

    // только для Admin/Operator
    "Клиент": ROLE === "Admin" || ROLE === "Operator" ? "client" : null,
};


// ==========================================================================
//     ОТРИСОВКА СТРОК
// ==========================================================================
function appendRows(tab, rows) {
    const tbody = document.getElementById(`tbody_${tab}`);

    rows.forEach((row) => {
        const tr = document.createElement("tr");

        tr.dataset.id = row["id"];
        const values = Object.values(row);
        if (values.length && values[0] === row["id"]) {
            values.shift();   // удалить ID из визуальной части
        }

        const keys = Object.keys(row).filter(k => k !== "id");  // ключи, кроме id
        tr.innerHTML = keys
            .map(k => `<td>${row[k] ?? ""}</td>`)
            .join("");

        tr.addEventListener("click", () => {
            const id = tr.dataset.id;
            if (!id) return;
            window.open(`/api/product/${id}/invoice/`, "_blank");
        });
        tbody.appendChild(tr);
    });
}

// ==========================================================================
//     L A Z Y   P A G I N A T I O N
// ==========================================================================
function resetLazy(tab) {
    const st = lazyState[tab];
    st.req = (st.req || 0) + 1; // инвалидируем все "старые" ответы fetch
    st.loading = false;
    st.finished = false;
    st.last_id = null;
    const tbody = document.getElementById(`tbody_${tab}`);
    if (tbody) tbody.innerHTML = "";
}


async function loadMore(tab, clear = false) {
    const st = lazyState[tab];
    if (st.loading || st.finished) return;

    const myReq = st.req || 0;   // снимок текущего запроса
    st.loading = true;

    // вкладка "Оплаты" не использует API товаров
    if (tab === "payments") {
        try {
            const tbody = document.getElementById(`tbody_${tab}`);
            const offset = tbody ? tbody.querySelectorAll("tr").length : 0;
            const data = await fetchPayments({offset});

            // если за время fetch был resetLazy() — игнорируем ответ
            if ((st.req || 0) !== myReq) {
                st.loading = false;
                return;
            }

            if (!data.results || data.results.length === 0) {
                st.finished = true;
                st.loading = false;
                return;
            }

            if (offset === 0) {
                buildPaymentsHeader();
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

    const tbody = document.getElementById(`tbody_${tab}`);
    const offset = tbody ? tbody.rows.length : 0;

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

        // если за время fetch был resetLazy() — игнорируем ответ
        if ((st.req || 0) !== myReq) {
            st.loading = false;
            return;
        }

        if (!data.results || data.results.length === 0) {
            st.finished = true;
            st.loading = false;
            return;
        }

        // если это первая загрузка → строим шапку
        if (offset === 0) {
            const first = data.results[0];
            const cols = Object.keys(first).filter(k => k !== "id");
            buildTableHeader(tab, cols);
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

function buildPaymentsHeader() {
    const table = document.querySelector("#tab-payments table");
    const cols = [
        {label: "Дата", field: "payment_date"},
        {label: "Тип операции", field: "operation_kind_label"},
        {label: "Вид оплаты", field: "operation_type"},
        {label: "Сумма USD", field: "amount_usd"},
        {label: "Комментарий", field: "comment"},
        {label: "Товары", field: "products"},
        {label: "Грузы", field: "cargos"}
    ];


    let html = "<thead><tr>";
    cols.forEach(col => {
        html += `<th data-field="${col.field}" class="sortable">${col.label}</th>`;
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
        tr.dataset.id = row.id;
        const order = [
            "payment_date",
            "operation_kind_label",   // Тип операции (Оплата/Начисление)
            "operation_type",         // Вид оплаты
            "amount_usd",             // Сумма USD
            "comment",                // Комментарий
            "products",               // Список ID товаров
            "cargos"                  // Список ID грузов
        ];

        tr.innerHTML = order.map(k => {
            let v = row[k];

            if (Array.isArray(v)) v = v.join(", ");
            return `<td>${v ?? ""}</td>`;
        }).join("");


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
    let headerText = mode === "add" ? "Новая операция" : "Редактирование операции";

    const html = `
    <div class="modal">
        <div class="modal-header">${headerText}</div>
        <div class="modal-body">
        <div class="modal-row">
            <label>Тип операции</label>
            <div style="display:flex;gap:12px;align-items:center;">
                <select id="opTypeSwitch">
                    <option value="payment">Оплата</option>
                    <option value="accrual">Начисление</option>
                </select>
                <select id="opKind"></select>
            </div>
        </div>

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
            <div class="modal-row">
                <label>Товары (ID)</label>
                <input id="payProducts" type="text"
                       placeholder="через запятую"
                       value="${(p.products || []).join(', ')}">
            </div>
            
            <div class="modal-row">
                <label>Грузы (ID)</label>
                <input id="payCargos" type="text"
                       placeholder="через запятую"
                       value="${(p.cargos || []).join(', ')}">
            </div>

        </div>

        <div class="modal-footer">
            <button class="btn-save">Сохранить</button>
            <button class="btn-cancel">Отмена</button>
        </div>
    </div>`;

    const inst = openModal({html, modalName: "payment", closable: true});
    const header = inst.modal.querySelector(".modal-header");
    const typeSelect = inst.modal.querySelector("#opTypeSwitch");
    const kindSelect = inst.modal.querySelector("#opKind");

    async function loadKinds() {
        const t = typeSelect.value;
        const url = t === "payment" ? "/api/payment-types/" : "/api/accrual-types/";
        const r = await fetch(url);
        const j = await r.json();
        kindSelect.innerHTML = j.map(i => `<option value="${i.id}">${i.name}</option>`).join("");
    }

    function applyHeaderColor() {
        header.classList.remove("payment", "accrual");
        header.classList.add(typeSelect.value);
    }
    // --- Режим EDIT: блокируем тип операции и клиента ---
    if (mode === "edit") {
        typeSelect.disabled = true;       // Тип операции
        document.getElementById("payClient").disabled = true;  // Клиент
    }

    applyHeaderColor();
    typeSelect.addEventListener("change", async () => {
        applyHeaderColor();
        await loadKinds();
    });
    if (mode === "edit") {
        typeSelect.value = (p.operation_kind === 1 ? "payment" : "accrual");
    }
    await loadKinds();
    if (mode === "edit") {
        kindSelect.value = p.operation_type_id;
    }


    const modal = inst.modal;
    // --- Блокировка кнопки Сохранить в режиме ADD ---
    function updateSaveState() {
        const saveBtn = modal.querySelector(".btn-save");
        const client = modal.querySelector("#payClient").value.trim();
        const amount = modal.querySelector("#payAmount").value.trim();

        // Кнопка недоступна, пока нет клиента или суммы
        saveBtn.disabled = (!client || !amount);
    }
    async function loadOperationKinds(kind) {
        const url = kind === "1"
            ? "/api/payment-types/"
            : "/api/accrual-types/";

        const r = await fetch(url);
        const list = await r.json();

        const sel = modal.querySelector("#payOperationKind");
        sel.innerHTML = list
            .map(x => `<option value="${x.id}">${x.name}</option>`)
            .join("");
    }

    // Переключение "Оплата/Начисление"
    // modal.querySelector("#payType").addEventListener("change", (e) => {
    //     loadOperationKinds(e.target.value);
    //
    //     const h = modal.querySelector(".modal-header");
    //     if (e.target.value === "1") {
    //         h.style.background = "#1e7ee6";   // синий — оплата
    //         h.style.color = "#fff";
    //     } else {
    //         h.style.background = "#a46a2d";   // коричневый — начисление
    //         h.style.color = "#fff";
    //     }
    // });


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
        // --- закрытие списка при клике мимо поля и выпадающего списка ---
        document.addEventListener("click", function closeClientDropdown(e) {
            if (!dropdown.contains(e.target) && e.target !== input) {
                dropdown.classList.add("hidden");
            }
        });
    }

    input.addEventListener("input", showDropdown);
    input.addEventListener("focus", () => {
        if (dropdown.innerHTML.trim() !== "") dropdown.classList.remove("hidden");
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
        // === Блокировка Сохранить для режима ADD ===
    const btnSave = modal.querySelector(".btn-save");

    function validateAddMode() {
        if (mode === "add") {
            const okClient = document.getElementById("payClient").value.trim() !== "";
            const okAmount = parseFloat(document.getElementById("payAmount").value) > 0;

            btnSave.disabled = !(okClient && okAmount);
        }
    }

    document.getElementById("payClient").addEventListener("input", validateAddMode);
    document.getElementById("payAmount").addEventListener("input", validateAddMode);

    // начальная проверка
    validateAddMode();

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
            payment_type: typeSelect.value === "payment" ? 1 : 2,
            operation_type_id: kindSelect.value,

            products: document.getElementById("payProducts").value
                .split(",")
                .map(s => s.trim())
                .filter(s => s),

            cargos: document.getElementById("payCargos").value
                .split(",")
                .map(s => s.trim())
                .filter(s => s),
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
    // Убираем знаки + и -
    modal.querySelector("#payAmount").addEventListener("input", (e) => {
        e.target.value = e.target.value.replace(/[+\-]/g, "");
    });
    document.getElementById("payRate").addEventListener("input", recalcUSD);
    if (mode === "add") {
        // Разблокируем поля (редактируем всё)
        typeSelect.disabled = false;
        kindSelect.disabled = false;
        document.getElementById("payClient").disabled = false;

        // Блокируем кнопку Save до заполнения
        updateSaveState();
        modal.querySelector("#payClient").addEventListener("input", updateSaveState);
        modal.querySelector("#payAmount").addEventListener("input", updateSaveState);
    }
    fetchExchangeRate();
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
    // === Клиент → скрываем фильтр по клиенту ===
    if (ROLE === "Client") {
        const block = document.getElementById("clientFilterBlock");
        if (block) block.style.display = "none";
    }

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
                    ["in_transit", "delivered", "payments"].forEach(tab => {
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
