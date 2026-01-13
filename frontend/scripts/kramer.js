// kramer.js
// Handles KramerBot personality, animations, and UI flair

// Helper: safely fetch elements when needed
function getSpeakingAnim() {
  return document.getElementById("kramer-speaking-animation");
}

function getKramerIcon() {
  return document.getElementById("kramer-icon");
}

// Start the speaking animation
export function kramerStartSpeaking() {
  const el = getSpeakingAnim();
  if (el) el.classList.add("kramer-speaking");
}

// Stop the speaking animation
export function kramerStopSpeaking() {
  const el = getSpeakingAnim();
  if (el) el.classList.remove("kramer-speaking");
}

// Optional: subtle idle hover effect
export function enableKramerIdle() {
  const icon = getKramerIcon();
  if (!icon) return;

  icon.addEventListener("mouseenter", () => {
    icon.style.transform = "scale(1.05)";
  });

  icon.addEventListener("mouseleave", () => {
    icon.style.transform = "scale(1)";
  });
}

// Kramer reacts when user sends a message
export function kramerReact() {
  const icon = getKramerIcon();
  if (!icon) return;

  icon.style.transform = "scale(1.1)";
  setTimeout(() => {
    icon.style.transform = "scale(1)";
  }, 150);
}
