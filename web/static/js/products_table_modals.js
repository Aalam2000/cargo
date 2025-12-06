// ===============================
//   Модалки товаров (новая версия)
//   Полная поддержка modal.css
//   Полное автодополнение клиента (как в home.js)
// ===============================
function getCSRF() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}
// ===============================
//   ADD PRODUCT MODAL
// ===============================
// ===============================
//   ADD PRODUCT MODAL — новая версия
// ===============================
function openProductAdd() {

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";

    overlay.innerHTML = `
        <div class="modal">

            <div class="modal-header">
                <span>Приём товара на склад</span>
            </div>

            <div class="modal-body modal-fields">

                <!-- CLIENT -->
                <div class="modal-row select-search-wrapper">
                    <label>Код клиента *</label>
                    <input id="add_client_code" 
                           class="select-search-input modal-input"
                           autocomplete="off"
                           placeholder="Введите код клиента...">
                </div>

                <!-- WAREHOUSE -->
                <div class="modal-row">
                    <label>Склад *</label>
                    <select id="add_warehouse" class="modal-input"></select>
                </div>

                <!-- CARGO TYPE -->
                <div class="modal-row">
                    <label>Тип груза *</label>
                    <select id="add_cargo_type" class="modal-input"></select>
                </div>

                <!-- CARGO STATUS -->
                <div class="modal-row">
                    <label>Статус груза *</label>
                    <select id="add_cargo_status" class="modal-input"></select>
                </div>

                <!-- PACKAGING -->
                <div class="modal-row">
                    <label>Тип упаковки *</label>
                    <select id="add_packaging" class="modal-input"></select>
                </div>

                <!-- PHOTO -->
                <div class="modal-row">
                    <label>Фото</label>
                    <div style="flex:1;">
                        <button id="btnAddPhoto" class="btn-secondary">Добавить фото</button>
                    </div>
                </div>

            </div>

            <div class="modal-footer">
                <button class="btn-secondary" id="add_close">Отмена</button>
                <button class="btn-primary" id="add_save">Создать</button>
            </div>

        </div>
    `;

    document.body.appendChild(overlay);

    // закрытие
    document.getElementById("add_close").onclick = () => {
        if (dropdown) dropdown.remove();
        overlay.remove();
    };


    // ===============================
    //  LOAD REFERENCES (SELECTS)
    // ===============================

    async function loadRef(url, selectEl) {
        const r = await fetch(url);
        const j = await r.json();
        (j.results || j).forEach(row => {
            const o = document.createElement("option");
            o.value = row.id;
            o.textContent = row.name;
            selectEl.appendChild(o);
        });
    }

    loadRef("/api/warehouses/?page_size=9999", document.getElementById("add_warehouse"));
    loadRef("/api/cargo-types/?page_size=9999", document.getElementById("add_cargo_type"));
    loadRef("/api/cargo-statuses/?page_size=9999", document.getElementById("add_cargo_status"));
    loadRef("/api/packaging-types/?page_size=9999", document.getElementById("add_packaging"));


    // ===============================
    //  AUTOCOMPLETE CLIENT (как было)
    // ===============================

    const input = overlay.querySelector("#add_client_code");

    let dropdown = document.createElement("div");
    dropdown.className = "client-autocomplete autocomplete-list hidden";
    overlay.appendChild(dropdown);

    let clientsCache = [];

    async function loadClients() {
        if (clientsCache.length) return clientsCache;
        const r = await fetch("/api/get_clients/?page_size=99999");
        const j = await r.json();
        clientsCache = j.results || j;
        return clientsCache;
    }

    async function showDropdown() {
        const q = input.value.trim().toLowerCase();
        const list = await loadClients();

        const filtered = q
            ? list.filter(c => c.client_code.toLowerCase().includes(q))
            : list.slice(0, 7);

        dropdown.innerHTML = filtered.length
            ? filtered.map(c => `<div class="autocomplete-item">${c.client_code}</div>`).join("")
            : `<div class="autocomplete-empty">Нет совпадений</div>`;

        dropdown.style.position = "absolute";
        const rect = input.getBoundingClientRect();
        dropdown.style.top = (rect.top + rect.height) + "px";
        dropdown.style.left = rect.left + "px";
        dropdown.style.width = rect.width + "px";
        dropdown.classList.remove("hidden");

        dropdown.querySelectorAll(".autocomplete-item").forEach(item => {
            item.addEventListener("mousedown", (e) => {
                e.stopPropagation();             // блокируем "закрытие"
                input.value = item.textContent.trim();
                dropdown.classList.add("hidden");
                setTimeout(() => dropdown.innerHTML = "", 50);
            });
        });
    }

    input.addEventListener("input", showDropdown);
    input.addEventListener("focus", showDropdown);

    document.addEventListener("mousedown", (e) => {
        if (e.target.closest(".autocomplete-item")) return;  // выбор элемента
        if (!dropdown.contains(e.target) && e.target !== input) {
            dropdown.classList.add("hidden");
        }
    });


    // ===============================
    //  SAVE
    // ===============================
    document.getElementById("add_save").onclick = async () => {

        const clientCode = input.value.trim();
        if (!clientCode) return;

        // ищем клиента
        const r1 = await fetch(`/api/get_clients/?search=${clientCode}`);
        const js1 = await r1.json();
        const client = js1.results.find(c => c.client_code === clientCode);
        if (!client) return;

        // генерируем код товара
        const r2 = await fetch("/api/generate/product/", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRF(),
            },
            body: JSON.stringify({ client_id: client.id })
        });
        const js2 = await r2.json();

        // отправляем CREATE
        await fetch("/api/products-table/", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRF()
            },
            body: JSON.stringify({
                client_id: client.id,
                product_code: js2.product_code,

                warehouse_id: document.getElementById("add_warehouse").value,
                cargo_type_id: document.getElementById("add_cargo_type").value,
                cargo_status_id: document.getElementById("add_cargo_status").value,
                packaging_type_id: document.getElementById("add_packaging").value,
            })
        });

        overlay.remove();
        PT_reset();
        PT_load();
    };

}

async function loadFullProductAndEdit(productId) {

    const r = await fetch(`/api/products-table/${productId}/`, {
        credentials: "include"
    });
    const full = await r.json();

    openProductEdit(full);
}


//   EDIT PRODUCT MODAL
function openProductEdit(product) {

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";

    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <span>Товар: ${product.product_code}</span>
            </div>

            <div class="modal-body">

                <div class="modal-row">
                    <button id="btnEditProduct" class="btn-primary" style="width:100%;">
                        ✏ Редактировать товар
                    </button>
                </div>

                <div class="modal-row">
                    <button id="btnCalcFinance" class="btn-secondary" style="width:100%;">
                        💰 Рассчитать финансы
                    </button>
                </div>

            </div>

            <div class="modal-footer">
                <button class="btn-secondary" id="edit_close">Закрыть</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    // закрытие
    document.getElementById("edit_close").onclick = () => overlay.remove();

    // обработчики кнопок
    document.getElementById("btnEditProduct").onclick = () => {
        overlay.remove();
        stubEditProduct(product);
    };

    document.getElementById("btnCalcFinance").onclick = () => {
        overlay.remove();
        stubCalcFinance(product);
    };
}

function stubEditProduct(product) {

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";

    overlay.innerHTML = `
        <div class="modal">

            <div class="modal-header">
                <span>Редактирование товара</span>
            </div>

            <div class="modal-body modal-fields">

                <!-- INFORM FIELDS -->
                <div class="modal-row">
                    <label>Код товара</label>
                    <div class="modal-info">${product.product_code}</div>
                </div>

                <div class="modal-row">
                    <label>Клиент</label>
                    <div class="modal-info">${product.client}</div>
                </div>

                <div class="modal-row">
                    <label>Дата записи</label>
                    <div class="modal-info">${product.record_date || ""}</div>
                </div>

                <!-- EDITABLE FIELDS -->

                <div class="modal-row">
                    <label>Описание</label>
                    <input id="edit_description" class="modal-input" value="${product.cargo_description || ""}">
                </div>

                <div class="modal-row">
                    <label>Пункт отправления</label>
                    <input id="edit_departure" class="modal-input" value="${product.departure_place || ""}">
                </div>

                <div class="modal-row">
                    <label>Пункт назначения</label>
                    <input id="edit_destination" class="modal-input" value="${product.destination_place || ""}">
                </div>

                <div class="modal-row">
                    <label>Вес</label>
                    <input id="edit_weight" class="modal-input" type="number" step="0.01" value="${product.weight || ""}">
                </div>

                <div class="modal-row">
                    <label>Объём</label>
                    <input id="edit_volume" class="modal-input" type="number" step="0.01" value="${product.volume || ""}">
                </div>

                <div class="modal-row">
                    <label>Стоимость товара</label>
                    <input id="edit_cost" class="modal-input" type="number" step="0.01" value="${product.cost || ""}">
                </div>

                <div class="modal-row">
                    <label>Срок доставки</label>
                    <input id="edit_delivery_time" class="modal-input" type="number" step="0.1" value="${product.delivery_time || ""}">
                </div>

                <div class="modal-row">
                    <label>Дата отправки</label>
                    <input id="edit_shipping_date" class="modal-input" type="date" value="${product.shipping_date || ""}">
                </div>

                <div class="modal-row">
                    <label>Дата доставки</label>
                    <input id="edit_delivery_date" class="modal-input" type="date" value="${product.delivery_date || ""}">
                </div>

                <div class="modal-row">
                    <label>Комментарий</label>
                    <textarea id="edit_comment" class="modal-input" style="height:70px;">${product.comment || ""}</textarea>
                </div>

            </div>

            <div class="modal-footer">
                <button class="btn-secondary" id="edit_cancel">Отмена</button>
                <button class="btn-primary" id="edit_save">Сохранить</button>
            </div>

        </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById("edit_cancel").onclick = () => overlay.remove();

    document.getElementById("edit_save").onclick = async () => {

        const payload = {
            cargo_description: document.getElementById("edit_description").value.trim(),
            departure_place: document.getElementById("edit_departure").value.trim(),
            destination_place: document.getElementById("edit_destination").value.trim(),
            weight: document.getElementById("edit_weight").value || null,
            volume: document.getElementById("edit_volume").value || null,
            cost: document.getElementById("edit_cost").value || null,
            delivery_time: document.getElementById("edit_delivery_time").value || null,
            shipping_date: document.getElementById("edit_shipping_date").value || null,
            delivery_date: document.getElementById("edit_delivery_date").value || null,
            comment: document.getElementById("edit_comment").value.trim(),
        };

        await fetch(`/api/products-table/${product.id}/`, {
            method: "PUT",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRF(),
            },
            body: JSON.stringify(payload)
        });


        overlay.remove();
        PT_reset();
        PT_load();
    };


}


function stubCalcFinance(product) {
    alert("ЗАГЛУШКА: расчет финансов для товара ID " + product.id);
}
