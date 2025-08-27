document.addEventListener("DOMContentLoaded", () => {
  const dataPorMoneda = JSON.parse(document.getElementById("data-por-moneda").textContent);
  const ctx = document.getElementById("graficoMoneda").getContext("2d");

  // Generar dinámicamente las opciones del select según dataPorMoneda
  const monedaSelect = document.getElementById("monedaSelect");
  monedaSelect.innerHTML = "";
  Object.keys(dataPorMoneda).forEach(moneda => {
    const option = document.createElement("option");
    option.value = moneda;
    option.textContent = moneda;
    monedaSelect.appendChild(option);
  });

  let currentMoneda = monedaSelect.value; // primera moneda de la lista

  function crearGrafico(moneda) {
    const data = dataPorMoneda[moneda];
    const fechas = data.map(d => d.fecha);
    const compra = data.map(d => d.compra);
    const venta = data.map(d => d.venta);

    if (window.miGrafico) window.miGrafico.destroy();

    window.miGrafico = new Chart(ctx, {
      type: "line",
      data: {
        labels: fechas,
        datasets: [
          {
            label: "Compra",
            data: compra,
            borderColor: "#4f46e5",
            backgroundColor: "rgba(79,70,229,0.2)",
            fill: true,
          },
          {
            label: "Venta",
            data: venta,
            borderColor: "#f59e0b",
            backgroundColor: "rgba(245,158,11,0.2)",
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { font: { size: 18 } } },
          tooltip: { titleFont: { size: 18 }, bodyFont: { size: 18 } },
        },
        scales: {
          y: { beginAtZero: false }, // se ajusta automáticamente según datos
        },
      },
    });
  }

  monedaSelect.addEventListener("change", (e) => crearGrafico(e.target.value));

  crearGrafico(currentMoneda);
});
