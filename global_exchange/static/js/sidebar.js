document.addEventListener("DOMContentLoaded", function () {
  // Sidebar Desktop
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebar-toggle");
  if (sidebar && toggle) {
    toggle.addEventListener("click", () => {
      console.log("sidebar clicked!");
      sidebar.classList.toggle("active");
      toggle.style.transform = sidebar.classList.contains("active")
        ? "rotate(180deg)"
        : "rotate(0deg)";
    });
  }

  // Menú Móvil
  const hamburger = document.getElementById("hamburger");
  const mobileMenu = document.getElementById("mobile-menu");
  if (hamburger && mobileMenu) {
    hamburger.addEventListener("click", () => {
      console.log("Hamburger clicked!"); // Para probar
      mobileMenu.classList.toggle("active");
      hamburger.innerHTML = mobileMenu.classList.contains("active")
        ? "&#10005;"
        : "&#9776;";
    });
  }
});
