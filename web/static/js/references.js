// web/static/js/references.js
// Универсальные таблицы — исправленная версия

document.addEventListener("DOMContentLoaded", () => {
    // Инициализируем только те карточки, у которых ЕСТЬ data-model и data-fields
    const tableCards = document.querySelectorAll(".table-card.table-container[data-model][data-fields]");

    tableCards.forEach(card => initTable(card));
});


// =========================================
//             ИНИЦИАЛИЗАЦИЯ ТАБЛИЦЫ
// =========================================
function initTable(card) {
    const model = card.dataset.model;
    const api = card.dataset.api;
    const fields = card.dataset.fields.split(",").map(x => x.trim());
    const pageSize = parseInt(card.dataset.pageSize || "10");

    const filterInput = card.querySelector("[data-filter]");
    const wrapper = card.querySelector(".table-wrapper");
    const table = card.querySelector(".dynamic-table");
    const btnAdd = card.querySelector("[data-action='add-record']");

    // состояние таблицы
    const state = {
        model,
        api,
        fields,
        pageSize,
        page: 1,
        loading: false,
        finished: false,
        search: "",
        sortField: "id",
        sortDir: "asc",
    };

    // ⚠ ВАЖНО: привязываем состояние к блоку таблицы
    card.__state = state;

    // создаём заголовок
    renderHeader(table, state);

    // загрузка первой страницы
    loadPage(card, state);

    // фильтр
    if (filterInput) {
        filterInput.addEventListener("input", () => {
            state.search = filterInput.value.trim();
            reloadTable(card, state);
        });
    }

    // пагинация по скроллу
    wrapper.addEventListener("scroll", () => {
        if (state.loading || state.finished) return;
        if (wrapper.scrollTop + wrapper.clientHeight >= wrapper.scrollHeight - 60) {
            loadPage(card, state);
        }
    });

    // кнопка Добавить
    if (btnAdd) {
        btnAdd.addEventListener("click", () => {
            const empty = {};
            state.fields.forEach(f => empty[f] = "");

            openEditModal({
                __mode: "create",
                __model: model,
                ...empty
            });
        });

    }
}


// =========================================
//             СОЗДАНИЕ ЗАГОЛОВКА
// =========================================
function renderHeader(table, state) {
    table.innerHTML = "";

    const thead = document.createElement("thead");
    const tr = document.createElement("tr");

    state.fields.forEach(field => {
        const th = document.createElement("th");
        th.textContent = prettify(field);
        th.dataset.field = field;
        th.style.cursor = "pointer";

        th.addEventListener("click", () => {
            if (state.sortField === field) {
                state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
            } else {
                state.sortField = field;
                state.sortDir = "asc";
            }
            reloadTable(table.closest(".table-card"), state);
        });

        tr.appendChild(th);
    });

    thead.appendChild(tr);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    table.appendChild(tbody);
}


// =========================================
//                 ЗАГРУЗКА
// =========================================
async function loadPage(card, state) {
    if (state.loading || state.finished) return;
    state.loading = true;

    const url = new URL(state.api, window.location.origin);
    url.searchParams.set("page", state.page);
    url.searchParams.set("page_size", state.pageSize);
    url.searchParams.set("search", state.search);
    url.searchParams.set("sort", state.sortField);
    url.searchParams.set("dir", state.sortDir);

    let data;
    try {
        data = await fetch(url).then(r => r.json());
    } catch (err) {
        console.error("Load error", err);
        state.loading = false;
        return;
    }

    const table = card.querySelector(".dynamic-table");
    const tbody = table.querySelector("tbody");

    data.results.forEach(row => {
        const tr = document.createElement("tr");
        tr.dataset.id = row.id;

        // Добавляем ячейки
        state.fields.forEach(f => {
            const td = document.createElement("td");
            td.textContent = row[f] ?? "";
            tr.appendChild(td);
        });

        // Клик по строке
        tr.addEventListener("click", async () => {
            const detailUrl = "/api/" + state.model + "/" + row.id + "/";
            const full = await fetch(detailUrl).then(r => r.json());

            openEditModal({
                __mode: "edit",
                __model: state.model,
                __id: row.id,
                ...full
            });
        });
        tbody.appendChild(tr);
    });

    // Были ли ещё страницы?
    if (data.page >= data.total_pages) {
        state.finished = true;
    } else {
        state.page++;
    }

    highlightSort(table, state);

    state.loading = false;
}


// =========================================
//            ПЕРЕЗАГРУЗКА ТАБЛИЦЫ
// =========================================
function reloadTable(card, state) {
    const table = card.querySelector(".dynamic-table");
    table.querySelector("tbody").innerHTML = "";

    state.page = 1;
    state.finished = false;

    highlightSort(table, state);
    loadPage(card, state);
}


// =========================================
//           ВИЗУАЛ СОРТИРОВКИ
// =========================================
function highlightSort(table, state) {
    const ths = table.querySelectorAll("thead th");

    ths.forEach(th => {
        th.classList.remove("active-sort-asc", "active-sort-desc");

        if (th.dataset.field === state.sortField) {
            th.classList.add(state.sortDir === "asc" ? "active-sort-asc" : "active-sort-desc");
        }
    });
}

// =========================================
//      МОДАЛКА РЕДАКТИРОВАНИЯ / ДОБАВЛЕНИЯ
//      (через window.openModal из base.js)
// =========================================
function openEditModal(context) {
    const mode = context.__mode;
    const model = context.__model;
    // Составляем HTML модалки
    let fieldsHtml = "";

    for (const key of Object.keys(context)) {
        if (key.startsWith("__")) continue;
        if (key === "id") continue;               // ⬅ скрыть системное поле
        if (key === "company") continue;          // ⬅ company задаётся автоматически

        const value = context[key] ?? "";
        const isLong = typeof value === "string" && value.length > 60;

        fieldsHtml += `
            <div class="modal-row">
                <label>${prettify(key)}</label>
                ${isLong
            ? `<textarea name="${key}" class="modal-input" rows="3">${value}</textarea>`
            : `<input type="text" name="${key}" class="modal-input" value="${value}">`
        }
            </div>
        `;
    }

    const html = `
        <div class="modal">
            <div class="modal-header">
                ${mode === "create" ? "Добавить запись" : "Редактировать запись"}
            </div>

            <div class="modal-body">
                <form id="refs-edit-form">
                    ${fieldsHtml}
                </form>
            </div>

            <div class="modal-footer">
                <button class="btn btn-secondary" data-modal-close>Отмена</button>
                <button class="btn btn-primary" id="modal-save">Сохранить</button>
            </div>
        </div>
    `;

    // Открываем через системную функцию
    const inst = openModal({
        html,
        modalName: `edit-${model}`,
        closable: true
    });

    // Обрабатываем сохранение
    inst.modal.querySelector("#modal-save").onclick = (ev) => {
        ev.preventDefault();
        saveEditModal(context, inst);
    };
}

// =========================================
//               СОХРАНЕНИЕ
// =========================================
async function saveEditModal(context, inst) {
    const model = context.__model;
    const mode = context.__mode;
    const id = context.__id;

    const form = inst.modal.querySelector("#refs-edit-form");
    const fd = new FormData(form);

    const payload = {};
    fd.forEach((v, k) => payload[k] = v);
    // компания всегда = компания пользователя (как число)
    payload.company = Number(window.USER_COMPANY_ID);


    const url = mode === "create"
        ? `/api/${model}/`
        : `/api/${model}/${id}/`;

    const res = await fetch(url, {
        method: mode === "create" ? "POST" : "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.getCsrf()
        },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        console.error(await res.text());
        alert("Ошибка сохранения");
        return;
    }

    // закрываем
    inst.close();

    // обновляем таблицу
    const card = document.querySelector(`.table-card[data-model="${model}"]`);
    if (card && card.__state) {
        reloadTable(card, card.__state);
    }
}

// =========================================
//        МОДАЛКА ДЛЯ РЕДАКТИРОВАНИЯ КОМПАНИИ
// =========================================
function openCompanyModal(data) {

    const html = `
        <div class="modal">
            <div class="modal-header">
                Компания
            </div>

            <div class="modal-body">
                <form id="company-edit-form">
                
                    <div class="modal-row">
                        <label>Название</label>
                        <input name="name" class="modal-input" type="text" value="${data.name ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>Регистрационный номер</label>
                        <input name="registration" class="modal-input" type="text" value="${data.registration ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>ИНН / Tax ID</label>
                        <input name="tax_id" class="modal-input" type="text" value="${data.tax_id ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>ОГРН / Registration №</label>
                        <input name="ogrn" class="modal-input" type="text" value="${data.ogrn ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>Юридический адрес</label>
                        <input name="legal_address" class="modal-input" type="text" value="${data.legal_address ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>Фактический адрес</label>
                        <input name="actual_address" class="modal-input" type="text" value="${data.actual_address ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>Ф.И.О. представителя</label>
                        <input name="representative_fullname" class="modal-input" type="text" value="${data.representative_fullname ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>Действует на основании</label>
                        <input name="representative_basis" class="modal-input" type="text" value="${data.representative_basis ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>Телефон</label>
                        <input name="phone" class="modal-input" type="text" value="${data.phone ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>Email</label>
                        <input name="email" class="modal-input" type="text" value="${data.email ?? ''}">
                    </div>
                
                    <div class="modal-row">
                        <label>Описание</label>
                        <textarea name="description" class="modal-input">${data.description ?? ''}</textarea>
                    </div>
                
                    <div class="modal-row">
                        <label>Префикс компании (2 буквы)</label>
                        <input name="prefix" maxlength="2" class="modal-input" type="text" value="${data.prefix ?? ''}">
                    </div>
                             
                    <div class="modal-row">
                        <label>Ф.И.О. директора</label>
                        <input name="director_fullname" class="modal-input" type="text" value="${data.director_fullname ?? ''}">
                    </div>
                
                </form>

            </div>


            <div class="modal-footer">
                <button class="btn btn-secondary" data-modal-close>Отмена</button>
                <button class="btn btn-primary" id="company-save">Сохранить</button>
            </div>
        </div>
    `;

    const inst = openModal({ html, modalName: "company-settings" });

    inst.modal.querySelector("#company-save").onclick = async () => {

        const form = inst.modal.querySelector("#company-edit-form");
        const fd = new FormData(form);

        const payload = {};
        fd.forEach((v, k) => payload[k] = v);
        // компания всегда = компания пользователя (как число)
        payload.company = Number(window.USER_COMPANY_ID);


        await fetch(`/api/company/${data.id}/update/`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": window.getCsrf()
            },
            body: JSON.stringify(payload)
        });

        inst.close();
        // обновляем заголовок в блоке
        const header = document.querySelector(".table-card-header h4");
        if (header) header.textContent = "Компания: " + payload.name;

        // обновляем JS переменную
        window.USER_COMPANY_NAME = payload.name;
    };
}


// =========================================
//  ВЫЗОВ МОДАЛКИ КОМПАНИИ (КНОПКА "ОТКРЫТЬ")
// =========================================
document.addEventListener("DOMContentLoaded", () => {
    const btnCompany = document.getElementById("btn-company-settings");

    if (btnCompany) {
        btnCompany.addEventListener("click", async () => {
            const companyId = window.USER_COMPANY_ID;

            const data = await fetch(`/api/company/${companyId}/`)
                .then(r => r.json());

            openCompanyModal(data);
        });
    }
});


// =========================================
//          ПРЕОБРАЗОВАНИЕ ИМЁН ПОЛЕЙ
// =========================================
function prettify(f) {
    if (f === "name") return "Название";
    if (f === "address") return "Адрес";
    if (f === "company") return "Компания";
    if (f === "description") return "Примечание";
    if (f === "default_amount") return "Сумма по умолчанию";
    return f;
}
