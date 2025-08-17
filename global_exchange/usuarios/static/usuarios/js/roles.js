document.addEventListener("DOMContentLoaded", function () {
  const permisosDisponibles = [
    "Crear",
    "Editar",
    "Eliminar",
    "Ver",
    "Exportar",
  ];
  const permisosContainer = document.getElementById("permisosContainer");
  let permisosSeleccionados = [];

  permisosDisponibles.forEach((permiso) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-outline-primary btn-sm m-1";
    btn.innerText = permiso;

    btn.addEventListener("click", function () {
      console.log("Botón de permiso clickeado:", permiso);
      if (permisosSeleccionados.includes(permiso)) {
        permisosSeleccionados = permisosSeleccionados.filter(
          (p) => p !== permiso
        );
        btn.classList.remove("active");
      } else {
        permisosSeleccionados.push(permiso);
        btn.classList.add("active");
      }
    });

    permisosContainer.appendChild(btn);
  });

  const modal = document.getElementById("roleModal");
  const rolNombre = document.getElementById("rolNombre");
  const rolDescripcion = document.getElementById("rolDescripcion");
  const modalTitle = document.getElementById("modalTitle");
  const roleForm = document.getElementById("roleForm");

  document
    .getElementById("btnNuevoRol")
    .addEventListener("click", function (e) {
      e.preventDefault();
      openModal();
    });

  document.querySelectorAll(".btnEditar").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const row = e.target.closest("tr");
      const nombre = row.cells[0].innerText;
      const descripcion = row.cells[1].innerText;
      const permisos = row.cells[2].innerText.split(", ").filter((p) => p);
      openModal(nombre, descripcion, permisos);
    });
  });

  document.querySelectorAll(".btnEliminar").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const row = e.target.closest("tr");
      const nombre = row.cells[0].innerText;
      alert("Se eliminaría el rol: " + nombre);
    });
  });

  function openModal(nombre = "", descripcion = "", permisos = []) {
    modal.style.display = "flex";
    rolNombre.value = nombre;
    rolDescripcion.value = descripcion;

    permisosSeleccionados = [];
    permisosContainer
      .querySelectorAll("button")
      .forEach((btn) => btn.classList.remove("active"));

    permisos.forEach((p) => {
      permisosSeleccionados.push(p);
      Array.from(permisosContainer.children).forEach((btn) => {
        if (btn.innerText === p) btn.classList.add("active");
      });
    });

    modalTitle.innerText = nombre ? "Editar Rol" : "Nuevo Rol";
  }

  document.getElementById("modalClose").addEventListener("click", function () {
    modal.style.display = "none";
  });
  window.addEventListener("click", function (event) {
    if (event.target == modal) modal.style.display = "none";
  });

  roleForm.addEventListener("submit", function (e) {
    e.preventDefault();
    alert(
      "Se guardaría el rol: " +
        rolNombre.value +
        "\nPermisos: " +
        permisosSeleccionados.join(", ")
    );
    modal.style.display = "none";
  });
});
