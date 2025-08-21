document.addEventListener("DOMContentLoaded", function () {
  const modal = document.getElementById("roleModal");
  const rolNombre = document.getElementById("rolNombre");
  const rolDescripcion = document.getElementById("rolDescripcion");
  const modalTitle = document.getElementById("modalTitle");
  const roleForm = document.getElementById("roleForm");

  // Botón para abrir modal de nuevo rol
  if (document.getElementById("btnNuevoRol")) {
    document
      .getElementById("btnNuevoRol")
      .addEventListener("click", function (e) {
        e.preventDefault();
        openModal();
      });
  }

  // Botón para editar rol
  if (document.querySelectorAll(".btnEditar")) {
    document.querySelectorAll(".btnEditar").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const row = e.target.closest("tr");
        const nombre = row.cells[0].innerText;
        const descripcion = row.cells[1].innerText;
        openModal(nombre, descripcion);
      });
    });
  }

  // Botón para eliminar rol
  if (document.querySelectorAll(".btnEliminar")) {
    document.querySelectorAll(".btnEliminar").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const row = e.target.closest("tr");
        const nombre = row.cells[0].innerText;
        alert("Se eliminaría el rol: " + nombre);
      });
    });
  }

  function openModal(nombre = "", descripcion = "") {
    modal.style.display = "flex";
    rolNombre.value = nombre;
    rolDescripcion.value = descripcion;
    modalTitle.innerText = nombre ? "Editar Rol" : "Nuevo Rol";
  }

  if (document.getElementById("modalClose")) {
    document.getElementById("modalClose").addEventListener("click", function () {
      modal.style.display = "none";
    });
  }
  window.addEventListener("click", function (event) {
    if (event.target == modal) modal.style.display = "none";
  });

});
