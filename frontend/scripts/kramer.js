// kramer.js
// Handles KramerBot personality, animations, and UI flair

// Pulse animation element
const speakingAnim = document.getElementById("kramer-speaking-animation");
const kramerIcon = document.getElementById("kramer-icon");

// Start the speaking animation
export function kramerStartSpeaking() {
  if (speakingAnim) {
    speakingAnim.classList.add("kramer-speaking");
  }
}

// Stop the speaking animation
export function kramerStopSpeaking() {
  if (speakingAnim) {
    speakingAnim.classList.remove("kramer-speaking");
  }
}

// Optional: subtle idle hover effect
export function enableKramerIdle() {
  if (!kramerIcon) return;

  kramerIcon.addEventListener("mouseenter", () => {
    kramerIcon.style.transform = "scale(1.05)";
  });

  kramerIcon.addEventListener("mouseleave", () => {
    kramerIcon.style.transform = "scale(1)";
  });
}

// Optional: Kramer reacts when user sends a message
export function kramerReact() {
  if (!kramerIcon) return;

  kramerIcon.style.transform = "scale(1.1)";
  setTimeout(() => {
    kramerIcon.style.transform = "scale(1)";
  }, 150);
}
