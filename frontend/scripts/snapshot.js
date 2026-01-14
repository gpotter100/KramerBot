// snapshot.js
import { BACKEND_URL } from "./config.js";

export async function loadSnapshot() {
  const loading = document.getElementById("snapshot-loading");
  const table = document.getElementById("snapshot-table");
  const head = document.getElementById("snapshot-head");
  const body = document.getElementById("snapshot-body");

  // Reset
  loading.classList.remove("hidden");
  table.classList.add("hidden");
  head.innerHTML = "";
  body.innerHTML = "";

  try {
    const res = await fetch(`${BACKEND_URL}/standings`);
    const data = await res.json();

    const allRows = data.standings;

    // Determine current season (first in list)
    const seasons = [...new Set(allRows.map(r => r[0]))];
    const currentSeason = seasons[0];

    const seasonRows = allRows.filter(r => r[0] === currentSeason);

    if (seasonRows.length === 0) {
      loading.textContent = "No snapshot data available.";
      return;
    }

    // Build header from first row (skip season label)
    const headerCells = seasonRows[0].slice(1);
    head.innerHTML = `<tr>${headerCells.map(h => `<th>${h}</th>`).join("")}</tr>`;

    // Top 4 teams (or fewer if needed)
    const topRows = seasonRows.slice(0, 4);

    body.innerHTML = topRows
      .map(r => {
        const cells = r.slice(1);
        return `<tr>${cells.map(c => `<td>${c}</td>`).join("")}</tr>`;
      })
      .join("");

    // Reveal table
    loading.classList.add("hidden");
    table.classList.remove("hidden");

  } catch (err) {
    console.error("Snapshot error:", err);
    loading.textContent = "Error loading snapshot.";
  }
}
