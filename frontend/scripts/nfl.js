import { API_BASE as BACKEND_URL } from "./config.js";

let currentData = [];
let currentSort = { column: null, direction: 1 };

const teamColors = {
  BUF: "#00338D", MIA: "#008E97", NE: "#002244", NYJ: "#125740",
  BAL: "#241773", CIN: "#FB4F14", CLE: "#311D00", PIT: "#FFB612",
  HOU: "#03202F", IND: "#002C5F", JAX: "#006778", TEN: "#4B92DB",
  DEN: "#FB4F14", KC: "#E31837", LV: "#000000", LAC: "#0080C6",
  DAL: "#041E42", NYG: "#0B2265", PHI: "#004C54", WAS: "#5A1414",
  CHI: "#0B162A", DET: "#0076B6", GB: "#203731", MIN: "#4F2683",
  ATL: "#A71930", CAR: "#0085CA", NO: "#D3BC8D", TB: "#D50A0A",
  ARI: "#97233F", LAR: "#003594", SF: "#AA0000", SEA: "#69BE28"
};

const positionIcons = {
  QB: "🧢",
  RB: "🏈",
  WR: "👟",
  TE: "👕"
};

// ===============================
// ELEMENTS
// ===============================
const seasonInput = document.getElementById("season-input");
const weekInput = document.getElementById("week-input");
const positionFilter = document.getElementById("position-filter");
const loadBtn = document.getElementById("load-btn");

const loadingIndicator = document.getElementById("loading-indicator");
const usageTable = document.getElementById("usage-table");
const usageBody = document.getElementById("usage-body");

const chartsContainer = document.getElementById("charts-container");
const touchesCanvas = document.getElementById("touches-chart");
const snapCanvas = document.getElementById("snap-chart");
const usageDonutCanvas = document.getElementById("usage-donut");

const topPanel = document.getElementById("top-performers");
const topList = document.getElementById("top-list");

const comparePanel = document.getElementById("compare-panel");
const compareSelect = document.getElementById("compare-select");
const compareMetrics = document.getElementById("compare-metrics");

let touchesChart = null;
let snapChart = null;
let usageDonutChart = null;

// ===============================
// INITIALIZE DROPDOWNS
// ===============================
async function initDropdowns() {
  try {
    const res = await fetch(`${BACKEND_URL}/nfl/seasons`);
    const seasons = await res.json();

    seasonInput.innerHTML = seasons
      .sort((a, b) => b - a)
      .map(y => `<option value="${y}">${y}</option>`)
      .join("");

    weekInput.innerHTML = Array.from({ length: 18 }, (_, i) =>
      `<option value="${i + 1}">${i + 1}</option>`
    ).join("");

  } catch (err) {
    console.error("Failed to load seasons:", err);
    seasonInput.innerHTML = `<option value="2024">2024</option>`;
  }
}

initDropdowns();

// ===============================
// EVENT BINDINGS
// ===============================
loadBtn.addEventListener("click", loadStats);
positionFilter.addEventListener("change", applyFilters);

document.querySelectorAll("#usage-table th").forEach(th => {
  th.addEventListener("click", () => sortBy(th.dataset.sort));
});

compareSelect.addEventListener("change", renderCompare);

// ===============================
// LOAD DATA
// ===============================
async function loadStats() {
  const season = Number(seasonInput.value);
  const week = Number(weekInput.value);

  usageTable.classList.add("hidden");
  chartsContainer.classList.add("hidden");
  topPanel.classList.add("hidden");
  comparePanel.classList.add("hidden");
  loadingIndicator.classList.remove("hidden");
  usageBody.innerHTML = "";
  topList.innerHTML = "";
  compareSelect.innerHTML = "";
  compareMetrics.innerHTML = "";

  try {
    const res = await fetch(`${BACKEND_URL}/nfl/player-usage/${season}/${week}`);
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);

    let data = await res.json();
    data = Array.isArray(data) ? data : [];

    if (data.length === 0) {
      usageBody.innerHTML = `<tr><td colspan="12">No data returned for this week.</td></tr>`;
      usageTable.classList.remove("hidden");
      return;
    }

    currentData = data.map(p => {
      const touches = (p.attempts ?? 0) + (p.receptions ?? 0);
      const totalYards =
        (p.passing_yards ?? 0) +
        (p.rushing_yards ?? 0) +
        (p.receiving_yards ?? 0);

      return {
        ...p,
        touches,
        total_yards: totalYards,
        efficiency: totalYards / Math.max(touches, 1),
        fantasy_per_touch: (p.fantasy_points_ppr ?? 0) / Math.max(touches, 1)
      };
    });

    populateCompareSelect(currentData);
    applyFilters();
    renderTopPerformers(currentData);

  } catch (err) {
    console.error("Error loading NFL data:", err);
    usageBody.innerHTML = `<tr><td colspan="12">Error loading data.</td></tr>`;
    usageTable.classList.remove("hidden");
  } finally {
    loadingIndicator.classList.add("hidden");
  }
}

// ===============================
// FILTERING
// ===============================
function applyFilters() {
  let filtered = [...currentData];

  const pos = positionFilter.value;
  if (pos !== "ALL") {
    filtered = filtered.filter(p => (p.position || "").toUpperCase() === pos);
  }

  if (currentSort.column) {
    filtered.sort((a, b) => {
      const valA = a[currentSort.column] ?? 0;
      const valB = b[currentSort.column] ?? 0;
      return (valA > valB ? 1 : -1) * currentSort.direction;
    });
  }

  renderTable(filtered);
  renderCharts(filtered);
}

// ===============================
// SORTING
// ===============================
function sortBy(column) {
  if (currentSort.column === column) {
    currentSort.direction *= -1;
  } else {
    currentSort.column = column;
    currentSort.direction = 1;
  }
  applyFilters();
}

// ===============================
// TABLE RENDERING
// ===============================
function renderTable(data) {
  usageBody.innerHTML = data
    .map(p => `
      <tr>
        <td>${positionIcons[p.position] || ""}</td>
        <td>${p.player_name}</td>
        <td>${p.team}</td>
        <td>${p.attempts}</td>
        <td>${p.receptions}</td>
        <td>${p.targets}</td>
        <td>${p.carries}</td>
        <td>${p.total_yards}</td>
        <td>${p.touchdowns}</td>
        <td>${p.fantasy_points_ppr}</td>
        <td>${p.touches}</td>
        <td>${p.efficiency.toFixed(2)}</td>
        <td>${p.fantasy_per_touch.toFixed(2)}</td>
      </tr>
    `)
    .join("");

  usageTable.classList.remove("hidden");
}

// ===============================
// TOP PERFORMERS
// ===============================
function renderTopPerformers(data) {
  const top = [...data]
    .sort((a, b) => b.fantasy_points_ppr - a.fantasy_points_ppr)
    .slice(0, 10);

  topList.innerHTML = top
    .map(p => `
      <li>
        ${positionIcons[p.position] || ""} 
        <strong>${p.player_name}</strong> — ${p.fantasy_points_ppr.toFixed(1)} pts
      </li>
    `)
    .join("");

  topPanel.classList.remove("hidden");
}

// ===============================
// COMPARE PANEL
// ===============================
function populateCompareSelect(data) {
  compareSelect.innerHTML = data
    .map(p => `<option value="${p.player_name}">${p.player_name}</option>`)
    .join("");

  comparePanel.classList.remove("hidden");
}

function renderCompare() {
  const name = compareSelect.value;
  const player = currentData.find(p => p.player_name === name);

  if (!player) return;

  compareMetrics.innerHTML = `
    <p><strong>${player.player_name}</strong></p>
    <p>Touches: ${player.touches}</p>
    <p>Total Yards: ${player.total_yards}</p>
    <p>Fantasy PPR: ${player.fantasy_points_ppr}</p>
    <p>Efficiency: ${player.efficiency.toFixed(2)}</p>
  `;
}

// ===============================
// CHARTS
// ===============================
function renderCharts(data) {
  const labels = data.map(p => p.player_name);
  const touches = data.map(p => p.touches);
  const snapPct = data.map(p => p.snap_pct || 0);

  if (touchesChart) touchesChart.destroy();
  if (snapChart) snapChart.destroy();
  if (usageDonutChart) usageDonutChart.destroy();

  touchesChart = new Chart(touchesCanvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Touches",
        data: touches,
        backgroundColor: "#4e79a7"
      }]
    }
  });

  snapChart = new Chart(snapCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Snap %",
        data: snapPct,
        borderColor: "#e15759"
      }]
    }
  });

  usageDonutChart = new Chart(usageDonutCanvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        label: "Touches",
        data: touches,
        backgroundColor: labels.map(() => "#59a14f")
      }]
    }
  });

  chartsContainer.classList.remove("hidden");
}
