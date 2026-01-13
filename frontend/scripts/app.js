function initSidebarNav() {
  const buttons = document.querySelectorAll(".nav-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      // For now, navigation is cosmetic. In future:
      // - change content of chat/visuals based on data-page
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initSidebarNav();
  initChat();
  initVisuals();
});
