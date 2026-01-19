// main.js — ES module entry point

import { initChat } from "./chat.js";
import { initUpload } from "./upload.js";
import { initVisuals } from "./visuals.js";

/* ============================================================
   SIDEBAR NAV
============================================================ */
function initSidebarNav() {
  const buttons = document.querySelectorAll(".nav-btn");
  if (!buttons.length) return;

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });
}

/* ============================================================
   MULTI-WEEK DROPDOWN INITIALIZER
============================================================ */
function initMultiWeekDropdown(selectEl) {
  if (!selectEl) return;

  selectEl.innerHTML = `
    <option value="ALL">ALL</option>
    ${Array.from({ length: 18 }, (_, i) => `<option value="${i + 1}">${i + 1}</option>`).join("")}
  `;

  selectEl.addEventListener("change", () => {
    const selected = Array.from(selectEl.selectedOptions).map(o => o.value);
    if (selected.includes("ALL")) {
      Array.from(selectEl.options).forEach(o => (o.selected = true));
    }
  });
}

/* ============================================================
   TAB SWITCHING (ONLY IF TABS EXIST)
============================================================ */
function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");

  if (!tabButtons.length || !tabPanels.length) return;

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;

      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanels.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(`tab-${target}`).classList.add("active");
    });
  });
}

/* ============================================================
   PAGE DETECTION
============================================================ */
function detectPage() {
  if (document.getElementById("usage-table")) return "weekly";
  if (document.getElementById("multi-usage-table")) return "multi-usage";
  if (document.getElementById("pbp-body") && document.getElementById("pbp-week-input")) return "multi-pbp";
  return "unknown";
}

/* ============================================================
   MAIN INITIALIZATION
============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  console.log("Main init running");

  const page = detectPage();
  console.log("Detected page:", page);

  initSidebarNav();
  initTabs();
  initChat();
  initUpload();
  initVisuals();

  // Initialize multi-week dropdowns ONLY if they exist
  initMultiWeekDropdown(document.getElementById("multi-week-input"));
  initMultiWeekDropdown(document.getElementById("pbp-multi-week-input"));
});

/* ============================================================
   SIDEBAR DROPDOWN TOGGLE
============================================================ */
document.querySelectorAll(".sidebar-dropdown .dropdown-toggle").forEach(btn => {
  btn.addEventListener("click", () => {
    const menu = btn.nextElementSibling;
    if (menu) {
      menu.style.display = menu.style.display === "flex" ? "none" : "flex";
    }
  });
});

