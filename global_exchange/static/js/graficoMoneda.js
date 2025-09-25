document.addEventListener("DOMContentLoaded", () => {
  console.log(document.getElementById("data-por-moneda")?.textContent || "{}");
  const dataPorMoneda = JSON.parse(
    document.getElementById("data-por-moneda")?.textContent || "{}"
  );

  const ctx = document.getElementById("graficoMoneda").getContext("2d");
  const monedaSelect = document.getElementById("monedaSelect");
  monedaSelect.innerHTML = "";

  // Si no hay monedas, creamos una opción genérica
  const monedas = Object.keys(dataPorMoneda);
  if (monedas.length === 0) {
    monedas.push("Moneda"); // nombre genérico
    dataPorMoneda["Moneda"] = []; // array vacío
  }

  monedas.forEach((moneda) => {
    const option = document.createElement("option");
    option.value = moneda;
    option.textContent = moneda;
    monedaSelect.appendChild(option);
  });

  let currentMoneda = monedaSelect.value;

  function crearGrafico(moneda) {
    const data = dataPorMoneda[moneda] || [];

    const fechas = data.map((d) => d.fecha);
    const compra = data.map((d) => d.compra);
    const venta = data.map((d) => d.venta);

    if (window.miGrafico) window.miGrafico.destroy();

    window.miGrafico = new Chart(ctx, {
      type: "line",
      data: {
        labels: fechas.length ? fechas : ["Sin datos"],
        datasets: [
          {
            label: "Compra",
            data: compra.length ? compra : [0],
            borderColor: "#4f46e5",
            backgroundColor: "rgba(79,70,229,0.2)",
            fill: true,
          },
          {
            label: "Venta",
            data: venta.length ? venta : [0],
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
          y: { beginAtZero: true },
        },
      },
    });
  }

  crearGrafico(currentMoneda);

  monedaSelect.addEventListener("change", (e) => crearGrafico(e.target.value));
});
