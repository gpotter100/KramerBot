import { API_BASE } from "./config.js";

async function refreshVisuals() {
  const chartBox = document.getElementById("visuals-box");
  if (!chartBox) return;

  try {
    const res = await fetch(`${API_BASE}/visuals/`);
    const data = await res.json();

    if (data.error) {
      chartBox.textContent = data.error;
      return;
    }

    const { labels, points } = data;
    chartBox.textContent = `Teams: ${labels.join(", ")} | Points: ${points.join(", ")}`;
  } catch (err) {
    chartBox.textContent = "Failed to load visuals.";
  }
}

function initVisuals() {
  console.log("initVisuals running");
  refreshVisuals();
}

export { refreshVisuals, initVisuals };

