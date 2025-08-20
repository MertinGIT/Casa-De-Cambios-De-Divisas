const ctx = document.getElementById("gananciasChart").getContext("2d");
const gananciasChart = new Chart(ctx, {
  type: "bar", // gráfico de barras (cuadrado)
  data: {
    labels: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
    datasets: [
      {
        label: "Ganancias en USD",
        data: [500, 700, 1200, 800, 1500, 2000, 1800],
        backgroundColor: "#007bff",
        borderRadius: 8, // esquinas redondeadas de las barras
      },
    ],
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});
