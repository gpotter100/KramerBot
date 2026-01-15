// app.js (ES module entry point)

import { sendChat } from "./chat.js";
import { uploadCSV } from "./upload.js";
import { refreshVisuals } from "./visuals.js";
import { loadStandingsPanel } from "./standings.js";
import { loadSnapshot } from "./snapshot.js";

import { 
  kramerStartSpeaking, 
  kramerStopSpeaking, 
  kramerReact 
} from "./kramer.js";

const API_BASE = "https://kramerbot.onrender.com";

// DOM elements
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const conversationBox = document.getElementById("conversation-box");
const fileInput = document.getElementById("csv-upload");
const uploadButton = document.getElementById("upload-button");

// -----------------------------
// Chat UI Helpers
// -----------------------------
export function appendMessage(who, text) {
  const div = document.createElement("div");
  div.classList.add("chat-message", who);

  const label = document.createElement("span");
  label.classList.add("sender-label");
  label.textContent = who === "user" ? "You: " : "Kramer: ";

  const content = document.createElement("span");
  content.classList.add("message-text");
  content.textContent = text;

  div.appendChild(label);
  div.appendChild(content);

  conversationBox.appendChild(div);
  conversationBox.scrollTop = conversationBox.scrollHeight;
}

// -----------------------------
// Event Listeners
// -----------------------------
chatSend.addEventListener("click", () => {
  kramerReact();
  sendChat(chatInput, conversationBox, appendMessage, API_BASE);
});

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    kramerReact();
    sendChat(chatInput, conversationBox, appendMessage, API_BASE);
  }
});

uploadButton.addEventListener("click", () => {
  uploadCSV(fileInput, appendMessage, API_BASE, refreshVisuals);
});

// -----------------------------
// PANEL SWITCHING
// -----------------------------
function showPanel(panelId) {
  document.querySelectorAll("main section").forEach(sec => {
    sec.classList.add("hidden");
  });

  const panel = document.getElementById(panelId);
  if (panel) panel.classList.remove("hidden");
}

document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const page = btn.dataset.page;

    // Update active state
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    // Switch panel
    if (page === "home") {
      showPanel("chat-panel");
    } 
    else if (page === "upload") {
      showPanel("upload-panel");
    } 
    else if (page === "standings") {
      showPanel("standings-panel");
      loadStandingsPanel(API_BASE);
    } 
    else if (page === "visuals") {
      showPanel("visual-panel");
      loadSnapshot(API_BASE);   // NEW: real data snapshot
      refreshVisuals();         // existing visuals loader
    } 
    else if (page === "stats") {
      showPanel("stats-panel");
    } 
    else if (page === "about") {
      showPanel("about-panel");
    }
  });
});

// -----------------------------
// Init Chat (future voice mode lives here)
// -----------------------------
export function initChat() {
  console.log("initChat() running…");
  if (chatInput) chatInput.focus();
}

// Run init on page load
document.addEventListener("DOMContentLoaded", initChat);
