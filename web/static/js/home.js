document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      contents.forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    });
  });

  const apply = document.getElementById("applyFilter");
  if (apply) {
    apply.addEventListener("click", () => {
      const params = new URLSearchParams();
      const productCode = document.getElementById("productFilter").value.trim();
      const cargoCode = document.getElementById("cargoFilter").value.trim();
      const client = document.getElementById("clientFilter") ? document.getElementById("clientFilter").value : "";
      if (productCode) params.append("product_code", productCode);
      if (cargoCode) params.append("cargo_code", cargoCode);
      if (client) params.append("client_id", client);
      window.location.href = "/home/?" + params.toString();
    });
  }
});
