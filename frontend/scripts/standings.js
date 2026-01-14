// standings.js
import { BACKEND_URL } from "./config.js";

export async function loadStandingsPanel() {
  const panel = document.getElementById("standings-panel");
  const seasonSelect = document.getElementById("season-select");
  const lastUpdatedEl = document.getElementById("last-updated");
  const head = document.getElementById("standings-head");
  const body = document.getElementById("standings-body");

  // Clear previous content
  head.innerHTML = "";
  body.innerHTML = "";
  seasonSelect.innerHTML = "";
  lastUpdatedEl.textContent = "Loading…";

  try {
    const res = await fetch(`${BACKEND_URL}/standings`);
    const data = await res.json();

    // Timestamp
    lastUpdatedEl.textContent = `Last updated: ${new Date(
      data.last_updated
    ).toLocaleString()}`;

    // Extract seasons
    const seasons = [...new Set(data.standings.map(row => row[0]))];

    // Populate dropdown
    seasonSelect.innerHTML = seasons
      .map(season => `<option value="${season}">${season}</option>`)
      .join("");

    // Render initial season
    renderSeason(data.standings, seasons[0]);

    // Change handler
    seasonSelect.addEventListener("change", () => {
      renderSeason(data.standings, seasonSelect.value);
    });

  } catch (err) {
    console.error("Error loading standings:", err);
    lastUpdatedEl.textContent = "Error loading standings.";
  }
}

function renderSeason(allRows, season) {
  const head = document.getElementById("standings-head");
  const body = document.getElementById("standings-body");

  const rows = allRows.filter(r => r[0] === season);

  if (rows.length === 0) {
    head.innerHTML = "";
    body.innerHTML = "<tr><td>No data available</td></tr>";
    return;
  }

  // Build header from first row (skip season label)
  const headerCells = rows[0].slice(1);
  head.innerHTML = `<tr>${headerCells.map(h => `<th>${h}</th>`).join("")}</tr>`;

  // Build body
  body.innerHTML = rows
    .map(r => {
      const cells = r.slice(1);
      return `<tr>${cells.map(c => `<td>${c}</td>`).join("")}</tr>`;
    })
    .join("");
}
