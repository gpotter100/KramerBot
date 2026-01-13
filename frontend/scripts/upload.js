import { API_BASE } from "./config.js";
import { refreshVisuals } from "./visuals.js";

async function uploadCSV() {
  const fileInput = document.getElementById("csv-upload");
  const file = fileInput.files[0];

  if (!file) {
    alert("No file selected.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/upload/`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    console.log("Upload response:", data);

    // Optional: show a message in the chat panel
    const box = document.getElementById("conversation-box");
    if (box) {
      const msg = document.createElement("div");
      msg.classList.add("chat-message", "kramer");
      msg.textContent = data.message || "Upload done. Probably.";
      box.appendChild(msg);
    }

    await refreshVisuals();
  } catch (err) {
    console.error("Upload failed:", err);
  }
}

function initUpload() {
  const btn = document.getElementById("upload-button");
  if (btn) {
    btn.addEventListener("click", uploadCSV);
  }
}

export { initUpload };
