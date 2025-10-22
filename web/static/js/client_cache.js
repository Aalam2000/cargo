window.clientData = [];
(async function () {
    // console.log("Заполняем начальные данные клиентов...");
    try {
        const resp = await fetch('/cargo_acc/api/get_clients/?search=&page_size=7&page=1');
        const data = await resp.json();
        if (data.results) {
            window.clientData = data.results;
            // console.log("Первые 7 клиентов:", window.clientData);
        }
    } catch (e) {
        console.error("Ошибка загрузки клиентов:", e);
    }
})();
