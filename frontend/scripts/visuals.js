// visuals.js

const API_BASE = "https://kramerbot-backend.onrender.com";

export async function refreshVisuals() {
  try {
    const res = await fetch(`${API_BASE}/visuals/`);
    const data = await res.json();

    if (data.error) {
      console.warn("No visuals available yet.");
      return;
    }

    console.log("Visuals:", data);
    // Future: render charts or tables here
  } catch (err) {
    console.error("Error loading visuals", err);
  }
}
