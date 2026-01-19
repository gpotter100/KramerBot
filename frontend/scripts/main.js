// main.js — ES module entry point

import { initChat } from "./chat.js";
import { initUpload } from "./upload.js";
import { initVisuals } from "./visuals.js";

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

document.addEventListener("DOMContentLoaded", () => {
  console.log("Main init running");

  initSidebarNav();
  initChat();
  initUpload();
  initVisuals();
});

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;

    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

    btn.classList.add("active");
    document.getElementById(`tab-${target}`).classList.add("active");
  });
});
