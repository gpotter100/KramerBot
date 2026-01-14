// visuals.js — handles bar chart + league snapshot
import { API_BASE } from "./config.js";

// -----------------------------------------------------
//  BAR CHART (existing functionality)
// -----------------------------------------------------
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

// -----------------------------------------------------
//  SNAPSHOT PANEL (new functionality)
// -----------------------------------------------------
async function loadSnapshot() {
  console.log("loadSnapshot running");

  const loadingEl = document.getElementById("snapshot-loading");
  const tableEl = document.getElementById("snapshot-table");
  const headEl = document.getElementById("snapshot-head");
  const bodyEl = document.getElementById("snapshot-body");

  if (!loadingEl || !tableEl || !headEl || !bodyEl) {
    console.warn("Snapshot DOM elements missing");
    return;
  }

  loadingEl.textContent = "Loading snapshot…";
  tableEl.classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/standings`);
    const data = await res.json();

    if (!data || !data.standings || data.standings.length === 0) {
      loadingEl.textContent = "No snapshot data available.";
      return;
    }

    // Data format: [season, col1, col2, col3, ...]
    const rows = data.standings;

    // Build header from first row (skip season)
    const headerCells = rows[0].slice(1);
    headEl.innerHTML = headerCells.map(h => `<th>${h}</th>`).join("");

    // Build body
    bodyEl.innerHTML = rows
      .map(r => {
        const cells = r.slice(1);
        return `<tr>${cells.map(c => `<td>${c}</td>`).join("")}</tr>`;
      })
      .join("");

    // Show table, hide loading
    loadingEl.textContent = "";
    tableEl.classList.remove("hidden");

  } catch (err) {
    console.error("Snapshot load error:", err);
    loadingEl.textContent = "Failed to load snapshot.";
  }
}

// -----------------------------------------------------
//  INIT
// -----------------------------------------------------
function initVisuals() {
  console.log("initVisuals running");

  refreshVisuals();   // existing bar chart
  loadSnapshot();     // new snapshot panel
}

export { refreshVisuals, initVisuals };

