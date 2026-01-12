const API_BASE = "https://kramerbot-backend.onrender.com";

const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const conversationBox = document.getElementById("conversation-box");
const fileInput = document.getElementById("csv-upload");      // add in HTML
const uploadButton = document.getElementById("upload-button"); // add in HTML
const visualsCanvas = document.getElementById("visuals-canvas"); // or container


function appendMessage(who, text) {
  const div = document.createElement("div");
  div.classList.add("chat-message", who);
  div.textContent = text;
  conversationBox.appendChild(div);
  conversationBox.scrollTop = conversationBox.scrollHeight;
}

async function sendChat() {
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  chatInput.value = "";

  try {
    const res = await fetch(`${API_BASE}/chat/`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ message })
    });
    const data = await res.json();
    const reply = data.reply || "I got nothing. Classic Kramer.";
    appendMessage("kramer", reply);
  } catch (err) {
    appendMessage("kramer", "Something went sideways. Very on brand.");
  }
}

chatSend.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendChat();
});

async function uploadCSV() {
  if (!fileInput.files.length) return;
  const file = fileInput.files[0];

  const formData = new FormData();
  formData.append("file", file);

  appendMessage("kramer", "Uploading your league… no guarantees.");

  try {
    const res = await fetch(`${API_BASE}/upload/`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    appendMessage("kramer", data.message || "Upload done. Probably.");
    await refreshVisuals();
  } catch (err) {
    appendMessage("kramer", "Upload blew up. That's… expected.");
  }
}

uploadButton.addEventListener("click", uploadCSV);

async function refreshVisuals() {
  try {
    const res = await fetch(`${API_BASE}/visuals/`);
    const data = await res.json();

    if (data.error) {
      // handle empty/error state
      // e.g., update visuals section text
      return;
    }

    // data.labels, data.points
    // Wire this to your fake bar chart (e.g., adjust heights or replace text)
    // For now you can just console.log:
    console.log("Visuals:", data);
  } catch (err) {
    console.error("Error loading visuals", err);
  }
}
