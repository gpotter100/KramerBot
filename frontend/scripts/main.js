// main.js — ES module entry point

import { initChat } from "./init.js";
import { refreshVisuals } from "./visuals.js";

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

// Optional wrapper for visuals if you want to modularize it
function initVisuals() {
  console.log("initVisuals running");
  refreshVisuals();
}

// Run everything on page load
document.addEventListener("DOMContentLoaded", () => {
  initSidebarNav();
  initChat();
  initVisuals();
});
