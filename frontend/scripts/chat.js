import { API_BASE } from "./config.js";

function appendMessage(text, sender = "kramer") {
  const box = document.getElementById("conversation-box");
  const msg = document.createElement("div");
  msg.classList.add("chat-message", sender);
  msg.textContent = text;
  box.appendChild(msg);
  box.scrollTop = box.scrollHeight;
}

function setSpeakingAnimation(on) {
  const anim = document.getElementById("kramer-speaking-animation");
  if (!anim) return;
  if (on) {
    anim.classList.add("kramer-speaking");
  } else {
    anim.classList.remove("kramer-speaking");
  }
}

async function handleUserMessage() {
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  input.value = "";
  setSpeakingAnimation(true);

  try {
    const res = await fetch(`${API_BASE}/chat/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();
    appendMessage(data.reply || "Kramer is speechless.", "kramer");
  } catch (err) {
    appendMessage("Something went sideways. Very on brand.", "kramer");
  } finally {
    setSpeakingAnimation(false);
  }
}

function initChat() {
  const intro = kramerIntroLines();
  intro.forEach(line => appendMessage(line, "kramer"));

  const sendBtn = document.getElementById("chat-send");
  const input = document.getElementById("chat-input");

  sendBtn.addEventListener("click", handleUserMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      handleUserMessage();
    }
  });
}

export { initChat };
