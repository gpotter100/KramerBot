// ============================================================
// MOBILE NAV CONTROLLER
// Works on every page that includes:
//   #mobile-nav-toggle
//   #mobile-nav
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("mobile-nav-toggle");
  const nav = document.getElementById("mobile-nav");

  if (!toggleBtn || !nav) return;

  // Toggle menu open/close
  toggleBtn.addEventListener("click", () => {
    nav.classList.toggle("hidden");
    document.body.classList.toggle("nav-open");
  });

  // Close menu when clicking outside
  document.addEventListener("click", (e) => {
    const clickedInsideNav = nav.contains(e.target);
    const clickedToggle = toggleBtn.contains(e.target);

    if (!clickedInsideNav && !clickedToggle && !nav.classList.contains("hidden")) {
      nav.classList.add("hidden");
      document.body.classList.remove("nav-open");
    }
  });

  // Close menu when clicking a link
  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.add("hidden");
      document.body.classList.remove("nav-open");
    });
  });
});
