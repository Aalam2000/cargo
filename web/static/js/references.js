// web/static/js/references.js
// Обновлённая версия: гарантированный скролл страницы + корректное управление overflow при модалке.

(function () {
  const MODELS = {
    'warehouses': { fields: ['name','address','company'], listApi: '/api/get_warehouses/?page_size=1000', api: '/api/warehouses/' },
    'cargo-types': { fields: ['name','description'], listApi: '/api/get_cargo_types/?page_size=1000', api: '/api/cargo-types/' },
    'cargo-statuses': { fields: ['name','description'], listApi: '/api/get_cargo_statuses/?page_size=1000', api: '/api/cargo-statuses/' },
    'packaging-types': { fields: ['name','description'], listApi: '/api/get_packaging_types/?page_size=1000', api: '/api/packaging-types/' }
  };

  let COMPANIES = [];

  document.addEventListener('DOMContentLoaded', async () => {
    try { COMPANIES = await fetchJson('/api/get_companies/?page_size=1000').then(r => r.results ?? r); } catch(e){ COMPANIES = []; }

    document.querySelectorAll('.ref-table').forEach(tbl => loadRefTable(tbl.dataset.model));

    document.querySelectorAll('.btn-add').forEach(btn => {
      btn.addEventListener('click', () => {
        const model = btn.dataset.model;
        openEditModal({__mode: 'create', __model: model});
      });
    });

    document.body.addEventListener('click', async (e) => {
      const tr = e.target.closest('tr[data-id]');
      if (!tr) return;
      const table = tr.closest('table');
      const model = table.dataset.model;
      const id = tr.dataset.id;
      try {
        const data = await fetchJson(`${MODELS[model].api}${id}/`);
        openEditModal({__mode: 'edit', __model: model, __id: id, ...data});
      } catch (err) {
        console.error(err);
        alert('Не удалось загрузить запись. Смотрите консоль.');
      }
    });
  });

  async function loadRefTable(model) {
    const table = document.querySelector(`.ref-table[data-model="${model}"]`);
    if (!table) return;
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = `<tr><td colspan="3">Загрузка...</td></tr>`;
    try {
      const list = await fetchJson(MODELS[model].listApi);
      const items = list.results ?? list;
      tbody.innerHTML = '';
      if (!items || items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">Нет данных</td></tr>';
        return;
      }
      for (const it of items) {
        const tr = document.createElement('tr');
        tr.dataset.id = it.id;
        tr.style.cursor = 'pointer';
        let cols = [];
        if (model === 'warehouses') cols = [it.name ?? '', it.address ?? '', it.company ?? (it.company_name ?? '')];
        else cols = [it.name ?? '', it.description ?? ''];
        for (const c of cols) {
          const td = document.createElement('td');
          td.textContent = c;
          td.style.padding = '10px 8px';
          td.style.fontSize = '15px';
          tr.appendChild(td);
        }
        tbody.appendChild(tr);
      }
    } catch (err) {
      console.error('loadRefTable', model, err);
      tbody.innerHTML = '<tr><td colspan="3">Ошибка загрузки</td></tr>';
    }
  }

  // Открытие модалки: блокируем скролл документа
  function openEditModal(context) {
    const model = context.__model;
    const fields = MODELS[model].fields;
    const root = document.getElementById('refs-modal-root');
    root.innerHTML = '';
    const overlay = document.createElement('div');
    overlay.className = 'refs-modal-overlay';
    overlay.style = `
      position:fixed;inset:0;background:rgba(0,0,0,0.45);display:flex;align-items:center;justify-content:center;z-index:2000;padding:12px;
    `;
    const dialog = document.createElement('div');
    dialog.style = `
      width: min(520px, 95%);max-height:90vh;background:#fff;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.25);overflow:auto;
      display:flex;flex-direction:column;
    `;
    const header = document.createElement('div');
    header.style = 'padding:14px 16px;border-bottom:1px solid #eef3ff;font-weight:700;background:#f6fbff;font-size:16px';
    header.textContent = context.__mode === 'create' ? 'Добавить запись' : 'Редактировать запись';
    dialog.appendChild(header);

    const body = document.createElement('div');
    body.style = 'padding:14px 16px;display:block;overflow:auto;';
    const form = document.createElement('form');
    form.id = 'refs-edit-form';
    form.onsubmit = (ev) => { ev.preventDefault(); saveFromModal(context, model); };

    for (const f of fields) {
      const row = document.createElement('div');
      row.style = 'margin-bottom:12px;display:flex;flex-direction:column;';
      const label = document.createElement('label');
      label.style = 'font-size:14px;font-weight:600;margin-bottom:6px;';
      label.textContent = prettifyField(f);
      let input;
      if (f === 'description' || f === 'address') {
        input = document.createElement('textarea');
        input.rows = 3;
        input.style = 'padding:12px;border:1px solid #e2e8ff;border-radius:8px;font-size:16px;resize:vertical';
      } else if (f === 'company') {
        input = document.createElement('select');
        input.style = 'padding:12px;border:1px solid #e2e8ff;border-radius:8px;font-size:16px';
        const emptyOpt = document.createElement('option'); emptyOpt.value=''; emptyOpt.textContent = '-- выбрать компанию --';
        input.appendChild(emptyOpt);
        for (const c of COMPANIES) {
          const o = document.createElement('option');
          o.value = c.id;
          o.textContent = c.name;
          input.appendChild(o);
        }
      } else {
        input = document.createElement('input');
        input.type = 'text';
        input.style = 'padding:12px;border:1px solid #e2e8ff;border-radius:8px;font-size:16px';
      }
      input.name = f;
      if (context.__mode === 'edit' && context[f] !== undefined && context[f] !== null) {
        if (f === 'company') {
          const v = context.company ?? context.company_id ?? context.company_name ?? (context.company && context.company.id);
          if (v) {
            if (typeof v === 'string' && isNaN(parseInt(v))) {
              const found = COMPANIES.find(c => c.name === v);
              if (found) input.value = found.id;
            } else input.value = v;
          }
        } else input.value = context[f];
      }
      row.appendChild(label);
      row.appendChild(input);
      form.appendChild(row);
    }

    // footer
    const footer = document.createElement('div');
    footer.style = 'padding:12px 16px;border-top:1px solid #eef3ff;background:#fafcff;display:flex;gap:8px;justify-content:flex-end;';
    const btnCancel = document.createElement('button');
    btnCancel.type = 'button';
    btnCancel.textContent = 'Отмена';
    btnCancel.style = 'padding:10px 14px;border-radius:8px;border:1px solid #cbd5e1;background:#fff;font-size:16px;cursor:pointer';
    btnCancel.onclick = () => closeModal();

    const btnSave = document.createElement('button');
    btnSave.type = 'submit';
    btnSave.textContent = 'Сохранить';
    btnSave.style = 'padding:10px 14px;border-radius:8px;border:none;background:#0b63d6;color:#fff;font-size:16px;cursor:pointer';

    form.appendChild(btnSave);
    footer.appendChild(btnCancel);
    dialog.appendChild(body);
    dialog.appendChild(footer);
    body.appendChild(form);

    overlay.appendChild(dialog);
    root.appendChild(overlay);

    // блокируем скролл основного документа
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';

    // клик вне диалога — закрыть
    overlay.addEventListener('click', (ev) => {
      if (ev.target === overlay) closeModal();
    });

    function closeModal() {
      // удаляем overlay и восстанавливаем скролл
      root.innerHTML = '';
      document.documentElement.style.overflow = '';
      document.body.style.overflow = '';
    }

    // expose closeModal для кнопки Отмена через глобальную функцию (закрытие из других мест)
    window.__refs_close_modal = closeModal;
  }

  async function saveFromModal(context, model) {
    const form = document.getElementById('refs-edit-form');
    const fd = new FormData(form);
    const payload = {};
    for (const [k, v] of fd.entries()) payload[k] = v;
    if (payload.company === '') delete payload.company;
    const api = MODELS[model].api;
    try {
      const csrftoken = getCsrf();
      let res;
      if (context.__mode === 'create') {
        res = await fetch(api, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
          body: JSON.stringify(payload)
        });
      } else {
        const id = context.__id;
        res = await fetch(`${api}${id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
          body: JSON.stringify(payload)
        });
      }
      if (!res.ok) {
        const err = await res.text();
        console.error('save error', err);
        alert('Ошибка сохранения. Смотрите консоль.');
        return;
      }
      await loadRefTable(model);
      // закрыть модал и восстановить скролл
      const root = document.getElementById('refs-modal-root');
      root.innerHTML = '';
      document.documentElement.style.overflow = '';
      document.body.style.overflow = '';
    } catch (err) {
      console.error(err);
      alert('Ошибка при сохранении. Смотрите консоль.');
    }
  }

  function prettifyField(name) {
    if (name === 'name') return 'Название';
    if (name === 'address') return 'Адрес';
    if (name === 'description') return 'Примечание';
    if (name === 'company') return 'Компания';
    return name;
  }

  async function fetchJson(url) {
    const res = await fetch(url, { credentials: 'same-origin' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function getCsrf() {
    const name = 'csrftoken=';
    const cookies = document.cookie.split(';').map(s => s.trim());
    for (const c of cookies) if (c.startsWith(name)) return c.substring(name.length);
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

})();
