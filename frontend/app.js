const API_BASE = "https://kramerbot-backend.onrender.com";

const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const conversationBox = document.getElementById("conversation-box");
const fileInput = document.getElementById("csv-upload");
const uploadButton = document.getElementById("upload-button");
const visualsCanvas = document.getElementById("visuals-canvas");


// -----------------------------
// Chat UI Helpers
// -----------------------------
function appendMessage(who, text) {
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
// Send Chat Message
// -----------------------------
async function sendChat() {
  console.log("sendChat fired");
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  chatInput.value = "";
  chatInput.disabled = true;

  // Add temporary "thinking" message
  const thinkingId = "kramer-thinking";
  appendMessage("kramer", "Hold on buddy… I'm thinking.");
  const thinkingEl = conversationBox.lastChild;
  thinkingEl.id = thinkingId;

  try {
    const res = await fetch(`${API_BASE}/chat/`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ message })
    });

    const data = await res.json();

    // Remove thinking message
    const thinkingNode = document.getElementById(thinkingId);
    if (thinkingNode) thinkingNode.remove();

    appendMessage("kramer", data.reply || "I got nothing. Classic Kramer.");
  } catch (err) {
    const thinkingNode = document.getElementById(thinkingId);
    if (thinkingNode) thinkingNode.remove();

    appendMessage("kramer", "Something went sideways. Very on brand.");
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
}

chatSend.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendChat();
});


// -----------------------------
// CSV Upload
// -----------------------------
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


// -----------------------------
// Refresh Visuals
// -----------------------------
async function refreshVisuals() {
  try {
    const res = await fetch(`${API_BASE}/visuals/`);
    const data = await res.json();

    if (data.error) {
      console.warn("No visuals available yet.");
      return;
    }

    console.log("Visuals:", data);
  } catch (err) {
    console.error("Error loading visuals", err);
  }
}
