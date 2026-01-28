// web/static/js/contract.js
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

async function postJson(url) {
  const csrftoken = getCookie("csrftoken") || "";
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrftoken,
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  const ct = (res.headers.get("content-type") || "").toLowerCase();

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);
  }

  if (!ct.includes("application/json")) {
    const text = await res.text();
    throw new Error(`Ожидали JSON, пришло: ${text.slice(0, 200)}`);
  }

  return await res.json();
}

document.addEventListener("DOMContentLoaded", async () => {
  const frame = document.getElementById("contract-frame");
  const btnSend = document.getElementById("btn-send-sign-link");

  // ВАЖНО: больше не fetch-им generate_contract.
  // iframe грузит PDF напрямую (inline application/pdf).
  if (frame) {
    frame.src = "/accounts/api/generate_contract/";
  }

  // Отправить на подпись (как было)
  if (btnSend) {
    btnSend.addEventListener("click", async () => {
      try {
        await postJson("/accounts/api/send_sign_link/");
        alert("На e-mail отправлена ссылка для подписания договора");
      } catch (e) {
        alert("Ошибка: " + e.message);
      }
    });
  }
});
