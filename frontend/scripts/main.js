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
