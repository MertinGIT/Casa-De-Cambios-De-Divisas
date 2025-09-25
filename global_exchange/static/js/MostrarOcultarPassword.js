document.addEventListener("DOMContentLoaded", function () {
  const toggleButtons = document.querySelectorAll(".toggle-password");

  toggleButtons.forEach((button) => {
    // Buscar el input password dentro del mismo form-group
    const formGroup = button.closest(".form-group");
    const passwordField = formGroup.querySelector(".password-field");
    const icon = button.querySelector("i");

    if (!passwordField) return;

    button.addEventListener("click", function () {
      if (passwordField.type === "password") {
        passwordField.type = "text";
        icon.classList.replace("bi-eye-slash", "bi-eye");
      } else {
        passwordField.type = "password";
        icon.classList.replace("bi-eye", "bi-eye-slash");
      }
    });
  });
});
