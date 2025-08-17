function toggleDropdown() {
  document.getElementById("userDropdown").classList.toggle("active");
}

document.addEventListener("click", function (e) {
  const dropdown = document.getElementById("userDropdown");
  const profile = document.querySelector(".user-info");

  if (!profile.contains(e.target)) {
    dropdown.classList.remove("active");
  }
});
