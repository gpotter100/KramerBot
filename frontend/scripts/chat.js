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

function handleUserMessage() {
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;

  // User message
  appendMessage(text, "user");
  input.value = "";

  // Kramer “thinking”
  setSpeakingAnimation(true);

  // Respond after a short delay
  setTimeout(() => {
    const reply = getRandomKramerResponse();
    appendMessage(reply, "kramer");
    setSpeakingAnimation(false);
  }, 500 + Math.random() * 600);
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
