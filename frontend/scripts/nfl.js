// ===============================
// IMPORT CONFIG
// ===============================
import { API_BASE as BACKEND_URL } from "./config.js";

// ===============================
// STATE
// ===============================
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

let touchesChart = null;
let snapChart = null;

// ===============================
// EVENT BINDINGS
// ===============================
loadBtn.addEventListener("click", loadStats);
positionFilter.addEventListener("change", applyFilters);

document.querySelectorAll("#usage-table th").forEach(th => {
  th.addEventListener("click", () => {
    const column = th.dataset.sort;
    sortBy(column);
  });
});

// ===============================
// LOAD DATA
// ===============================
async function loadStats() {
  const season = seasonInput.value;
  const week = weekInput.value;

  usageTable.classList.add("hidden");
  chartsContainer.classList.add("hidden");
  loadingIndicator.classList.remove("hidden");
  usageBody.innerHTML = "";

  try {
    const res = await fetch(`${BACKEND_URL}/nfl/player-usage/${season}/${week}`);
    if (!res.ok) {
      throw new Error(`Backend returned ${res.status}`);
    }

    const data = await res.json();
    currentData = Array.isArray(data) ? data : [];

    if (currentData.length === 0) {
      usageBody.innerHTML = `<tr><td colspan="7">No data returned for this week.</td></tr>`;
      usageTable.classList.remove("hidden");
      loadingIndicator.classList.add("hidden");
      return;
    }

    applyFilters();
  } catch (err) {
    console.error("Error loading NFL data:", err);
    usageBody.innerHTML = `<tr><td colspan="7">Error loading data.</td></tr>`;
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

  // If a sort is active, keep it applied
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
  usageBody.innerHTML = data.map(player => {
    const color = teamColors[player.team] || "#444";

    return `
      <tr>
        <td>${player.player_name}</td>
        <td><span class="team-accent" style="background:${color}">${player.team}</span></td>
        <td>${player.position}</td>
        <td>${player.attempts ?? 0}</td>
        <td>${player.receptions ?? 0}</td>
        <td>${player.targets ?? 0}</td>
        <td>${player.snap_pct ? player.snap_pct.toFixed(1) : 0}</td>
      </tr>
    `;
  }).join("");

  usageTable.classList.remove("hidden");
}

// ===============================
// CHARTS
// ===============================
function renderCharts(data) {
  if (!touchesCanvas || !snapCanvas) return;

  const labels = data.map(p => p.player_name);
  const touches = data.map(p => (p.attempts ?? 0) + (p.receptions ?? 0));
  const snaps = data.map(p => p.snap_pct ?? 0);

  if (touchesChart) touchesChart.destroy();
  if (snapChart) snapChart.destroy();

  touchesChart = new Chart(touchesCanvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Touches",
        data: touches,
        backgroundColor: "#66ccff"
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#d9eaff" } },
        y: { ticks: { color: "#d9eaff" } }
      }
    }
  });

  snapChart = new Chart(snapCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Snap %",
        data: snaps,
        borderColor: "#66ccff",
        backgroundColor: "rgba(102, 204, 255, 0.2)",
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#d9eaff" } } },
      scales: {
        x: { ticks: { color: "#d9eaff" } },
        y: { ticks: { color: "#d9eaff" } }
      }
    }
  });

  chartsContainer.classList.remove("hidden");
}
