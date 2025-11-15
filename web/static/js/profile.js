// web/static/js/profile.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("profile-form");
  const btnContract = document.getElementById("btn-contract");
  const btnSign = document.getElementById("btn-sign");
  const btnPay = document.getElementById("btn-pay");

  // === Сохранение профиля без перезагрузки ===
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        const res = await fetch(window.location.pathname, {
          method: "POST",
          body: fd,
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (res.ok) {
          alert("✅ Профиль успешно сохранён");
        } else {
          alert("Ошибка при сохранении профиля");
        }
      } catch (err) {
        alert("Ошибка сети: " + err.message);
      }
    });
  }

  // === Генерация и открытие договора ===
  if (btnContract) {
    btnContract.addEventListener("click", async () => {
      try {
        const res = await fetch("/accounts/api/generate_contract/", { method: "POST" });
        const data = await res.json();
        if (data.url) window.open(data.url, "_blank");
        else alert("Не удалось создать договор");
      } catch (e) {
        alert("Ошибка: " + e.message);
      }
    });
  }

  // === Отправка ссылки для электронной подписи ===
  if (btnSign) {
    btnSign.addEventListener("click", async () => {
      try {
        const res = await fetch("/accounts/api/send_sign_link/", { method: "POST" });
        if (!res.ok) throw new Error("Ошибка отправки ссылки для подписи");
        alert("На ваш e-mail отправлена ссылка для подписания договора");
      } catch (e) {
        alert("Ошибка: " + e.message);
      }
    });
  }

  // === Генерация QR для оплаты ===
  if (btnPay) {
    btnPay.addEventListener("click", async () => {
      try {
        const res = await fetch("/accounts/api/generate_qr_payment/", { method: "POST" });
        const data = await res.json();
        if (data.qr_url) {
          const html = `
            <div class="modal">
              <div class="modal-header">Оплата по QR</div>
              <div class="modal-body text-center">
                <img src="${data.qr_url}" alt="QR" style="width:280px;height:280px;display:block;margin:auto;">
                <p>Отсканируйте QR для оплаты через СБП</p>
              </div>
              <div class="modal-footer">
                <button class="btn btn-cancel" data-modal-close>Закрыть</button>
              </div>
            </div>`;
          openModal({ html, modalName: "qr" });
        } else alert("Не удалось получить QR-код");
      } catch (e) {
        alert("Ошибка: " + e.message);
      }
    });
  }
});

// === Переключение типа клиента ===
function toggleClientType() {
    const type = document.querySelector('input[name="client_type"]:checked').value;
    const blockIndividual = document.getElementById("block-individual");
    const blockCompany = document.getElementById("block-company");

    if (type === "individual") {
        blockIndividual.style.display = "block";
        blockCompany.style.display = "none";
    } else {
        blockIndividual.style.display = "none";
        blockCompany.style.display = "block";
    }
}

// === Инициализация блока типов клиента ===
const typeInputs = document.querySelectorAll('input[name="client_type"]');

if (typeInputs.length > 0) {
    // Если пользователь — Клиент, у него есть переключатель
    toggleClientType();

    typeInputs.forEach(r => {
        r.addEventListener("change", toggleClientType);
    });
}