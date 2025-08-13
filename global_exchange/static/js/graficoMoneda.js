// static/js/graficoMoneda.js

document.addEventListener("DOMContentLoaded", () => {
  const dataPorMoneda = JSON.parse(
    document.getElementById("data-por-moneda").textContent
  );
  const ctx = document.getElementById("graficoMoneda").getContext("2d");
  let currentMoneda = "USD";

  function crearGrafico(moneda) {
    const data = dataPorMoneda[moneda];
    const fechas = data.map((d) => d.fecha);
    const compra = data.map((d) => d.compra);
    const venta = data.map((d) => d.venta);

    if (window.miGrafico) {
      window.miGrafico.destroy();
    }

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
        scales: {
          y: {
            min: 7500,
            max: 9000,
          },
        },
      },
    });
  }

  document.getElementById("monedaSelect").addEventListener("change", (e) => {
    crearGrafico(e.target.value);
  });

  crearGrafico(currentMoneda);
});
