// init.js
export function initChat() {
  console.log("initChat running");
  const chatInput = document.getElementById("chat-input");
  if (chatInput) chatInput.focus();
}
