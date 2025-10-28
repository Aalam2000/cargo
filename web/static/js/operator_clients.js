// === operator_clients.js ===

let clients = [];
let selectedClient = null;

async function fetchClients(search = "") {
    document.getElementById("loader").style.display = "block";
    const res = await fetch(`/cargo_acc/api/get_clients/?search=${encodeURIComponent(search)}`);
    const data = await res.json();
    clients = data.results || [];
    renderClients();
    document.getElementById("loader").style.display = "none";
}

function renderClients() {
    const tbody = document.getElementById("clients-body");
    tbody.innerHTML = "";

    clients.forEach(c => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${c.client_code}</td>
            <td>${c.company || ""}</td>
            <td>${c.description || ""}</td>
            <td class="balance-cell" id="bal-${c.id}">—</td>
            <td><button class="btn-table" onclick="openPaymentModal('${c.client_code}')">💵 Оплата</button></td>
        `;
        tbody.appendChild(tr);
        loadBalance(c.id);
    });
}

// Получение баланса клиента (через API)
async function loadBalance(clientId) {
    try {
        const res = await fetch(`/api/client_balance/${clientId}/`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        document.getElementById(`bal-${clientId}`).textContent = data.balance_usd?.toFixed(2) ?? "0.00";
    } catch {
        document.getElementById(`bal-${clientId}`).textContent = "—";
    }
}

// === Модальное окно оплаты ===
function openPaymentModal(clientCode) {
    selectedClient = clientCode;
    document.getElementById("payment-client").value = clientCode;
    document.getElementById("payment-modal").style.display = "block";
    document.getElementById("modal-overlay").style.display = "block";
}

function closePaymentModal() {
    document.getElementById("payment-modal").style.display = "none";
    document.getElementById("modal-overlay").style.display = "none";
}

// === Сохранение оплаты ===
async function savePayment() {
    const amount = parseFloat(document.getElementById("payment-amount").value);
    const comment = document.getElementById("payment-comment").value;

    if (!selectedClient || isNaN(amount) || amount <= 0) {
        alert("Введите корректную сумму");
        return;
    }

    const payload = {
        client_code: selectedClient,
        amount_usd: amount,
        comment: comment
    };

    try {
        const res = await fetch("/api/create_payment/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            alert("Платеж добавлен успешно");
            closePaymentModal();
            fetchClients();
        } else {
            alert("Ошибка: " + (data.message || "Не удалось сохранить платёж"));
        }
    } catch (e) {
        alert("Ошибка соединения с сервером");
    }
}

// === Инициализация ===
document.addEventListener("DOMContentLoaded", () => {
    fetchClients();

    document.getElementById("filter-client").addEventListener("input", e => {
        const q = e.target.value.trim();
        fetchClients(q);
    });

    document.getElementById("refresh-btn").addEventListener("click", () => fetchClients());
    document.getElementById("payment-save").addEventListener("click", savePayment);
    document.getElementById("payment-cancel").addEventListener("click", closePaymentModal);
    document.getElementById("modal-overlay").addEventListener("click", closePaymentModal);
});
