document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("toggleContactsBtn");
  const panel = document.getElementById("contactsPanel");

  toggleBtn.addEventListener("click", () => {
    panel.classList.toggle("opacity-0");
    panel.classList.toggle("pointer-events-none");
  });
});
