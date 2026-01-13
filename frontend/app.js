// app.js (ES module entry point)

import { sendChat } from "./chat.js";
import { uploadCSV } from "./upload.js";
import { refreshVisuals } from "./visuals.js";
import { 
  kramerStartSpeaking, 
  kramerStopSpeaking, 
  kramerReact 
} from "./kramer.js";

const API_BASE = "https://kramerbot-backend.onrender.com";

// DOM elements
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const conversationBox = document.getElementById("conversation-box");
const fileInput = document.getElementById("csv-upload");
const uploadButton = document.getElementById("upload-button");
const visualsCanvas = document.getElementById("visuals-canvas");

// Debug logs
console.log("chatInput:", chatInput);
console.log("chatSend:", chatSend);
console.log("conversationBox:", conversationBox);

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
// Init Chat (future voice mode lives here)
// -----------------------------
export function initChat() {
  console.log("initChat() running…");

  // Future: voice recognition setup
  // Future: wake-word listener
  // Future: Kramer intro line
  // Future: audio unlock gesture

  if (chatInput) chatInput.focus();
}

// Run init on page load
document.addEventListener("DOMContentLoaded", initChat);
