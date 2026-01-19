// main.js — ES module entry point

import { initChat } from "./chat.js";
import { initUpload } from "./upload.js";
import { initVisuals } from "./visuals.js";

/* ============================================================
   SIDEBAR NAV
============================================================ */
function initSidebarNav() {
  const buttons = document.querySelectorAll(".nav-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      // Future: switch content based on data-page
    });
  });
}

/* ============================================================
   MULTI-WEEK DROPDOWN INITIALIZER
============================================================ */
function initMultiWeekDropdown(selectEl) {
  if (!selectEl) return;

  // Populate with ALL + weeks 1–18
  selectEl.innerHTML = `
    <option value="ALL">ALL</option>
    ${Array.from({ length: 18 }, (_, i) => `<option value="${i + 1}">${i + 1}</option>`).join("")}
  `;

  // If ALL is selected → select everything
  selectEl.addEventListener("change", () => {
    const selected = Array.from(selectEl.selectedOptions).map(o => o.value);
    if (selected.includes("ALL")) {
      Array.from(selectEl.options).forEach(o => (o.selected = true));
    }
  });
}

/* ============================================================
   TAB SWITCHING
============================================================ */
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;

      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(`tab-${target}`).classList.add("active");
    });
  });
}

/* ============================================================
   MAIN INITIALIZATION
============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  console.log("Main init running");

  initSidebarNav();
  initTabs();
  initChat();
  initUpload();
  initVisuals();

  // Initialize multi-week dropdowns
  initMultiWeekDropdown(document.getElementById("multi-week-input"));
  initMultiWeekDropdown(document.getElementById("pbp-multi-week-input"));
});

// Sidebar dropdown toggle
document.querySelectorAll(".sidebar-dropdown .dropdown-toggle").forEach(btn => {
  btn.addEventListener("click", () => {
    const menu = btn.nextElementSibling;
    menu.style.display = menu.style.display === "flex" ? "none" : "flex";
  });
});
