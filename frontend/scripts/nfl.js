import { API_BASE as BACKEND_URL } from "./config.js";

let currentData = [];
let currentSort = { column: null, direction: 1 };

// ===============================
// SAFE ACCESS HELPERS
// ===============================
const safe = (v, fallback = "—") =>
  v === undefined || v === null || Number.isNaN(v) ? fallback : v;

const safeNum = (v) =>
  typeof v === "number" && !Number.isNaN(v) ? v : 0;

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
// INIT DROPDOWNS
// ===============================
async function initDropdowns() {
  const res = await fetch(`${BACKEND_URL}/nfl/seasons`);
  const seasons = await res.json();

  seasonInput.innerHTML = seasons
    .sort((a, b) => b - a)
    .map(y => `<option value="${y}">${y}</option>`)
    .join("");

  weekInput.innerHTML = Array.from({ length: 18 }, (_, i) =>
    `<option value="${i + 1}">${i + 1}</option>`
  ).join("");
}

initDropdowns();

// ===============================
// EVENTS
// ===============================
loadBtn.addEventListener("click", loadStats);
positionFilter.addEventListener("change", applyFilters);

// ===============================
// LOAD DATA (DEBUG VERSION)
// ===============================
async function loadStats() {
  const season = Number(seasonInput.value);
  const week = Number(weekInput.value);

  usageBody.innerHTML = "";
  loadingIndicator.classList.remove("hidden");

  try {
    const res = await fetch(`${BACKEND_URL}/nfl/player-usage/${season}/${week}`);
    const data = await res.json();

    console.group("📦 RAW BACKEND PAYLOAD");
    console.log("Rows:", data.length);
    console.log("First row:", data[0]);
    console.log("Keys:", Object.keys(data[0] || {}));
    console.groupEnd();

    currentData = data.map(p => {
      const touches = safeNum(p.attempts) + safeNum(p.receptions);
      const totalYards =
        safeNum(p.passing_yards) +
        safeNum(p.rushing_yards) +
        safeNum(p.receiving_yards);

      return {
        ...p,
        touches,
        total_yards: totalYards,
        efficiency: touches ? totalYards / touches : 0,
        fantasy_per_touch: touches
          ? safeNum(p.fantasy_points_ppr) / touches
          : 0
      };
    });

    applyFilters();
    renderTopPerformers(currentData);
    populateCompareSelect(currentData);

  } catch (err) {
    console.error("❌ LOAD ERROR:", err);
    usageBody.innerHTML = `<tr><td colspan="15">Error loading data</td></tr>`;
  } finally {
    loadingIndicator.classList.add("hidden");
  }
}

// ===============================
// FILTERING
// ===============================
function applyFilters() {
  let filtered = [...currentData];

  if (positionFilter.value !== "ALL") {
    filtered = filtered.filter(
      p => (p.position || "").toUpperCase() === positionFilter.value
    );
  }

  renderTable(filtered);
  renderCharts(filtered);
}

// ===============================
// TABLE RENDER (SAFE)
// ===============================
function renderTable(data) {
  usageBody.innerHTML = data.map(p => `
    <tr>
      <td>${safe(p.position)}</td>
      <td>${safe(p.player_name)}</td>
      <td>${safe(p.team)}</td>
      <td>${safe(p.attempts)}</td>
      <td>${safe(p.receptions)}</td>
      <td>${safe(p.targets)}</td>
      <td>${safe(p.carries)}</td>
      <td>${safe(p.total_yards)}</td>
      <td>${safe(p.touchdowns)}</td>
      <td>${safe(p.fantasy_points)}</td>
      <td>${safe(p.fantasy_points_half)}</td>
      <td>${safe(p.fantasy_points_ppr)}</td>
      <td>${safe(p.touches)}</td>
      <td>${safe(p.efficiency.toFixed?.(2))}</td>
      <td>${safe(p.fantasy_per_touch.toFixed?.(2))}</td>
    </tr>
  `).join("");

  usageTable.classList.remove("hidden");
}

// ===============================
// TOP PERFORMERS (SAFE)
// ===============================
function renderTopPerformers(data) {
  const top = [...data]
    .sort((a, b) => safeNum(b.fantasy_points_ppr) - safeNum(a.fantasy_points_ppr))
    .slice(0, 10);

  topList.innerHTML = top.map(p => `
    <li>
      <strong>${safe(p.player_name)}</strong> — ${safe(p.fantasy_points_ppr)} pts
    </li>
  `).join("");

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

// ===============================
// CHARTS (SAFE)
// ===============================
function renderCharts(data) {
  if (!data.length) return;

  const labels = data.map(p => p.player_name || "—");
  const touches = data.map(p => safeNum(p.touches));
  const snapPct = data.map(p => safeNum(p.snap_pct));

  if (touchesChart) touchesChart.destroy();
  if (snapChart) snapChart.destroy();
  if (usageDonutChart) usageDonutChart.destroy();

  touchesChart = new Chart(touchesCanvas, {
    type: "bar",
    data: { labels, datasets: [{ label: "Touches", data: touches }] }
  });

  snapChart = new Chart(snapCanvas, {
    type: "line",
    data: { labels, datasets: [{ label: "Snap %", data: snapPct }] }
  });

  usageDonutChart = new Chart(usageDonutCanvas, {
    type: "doughnut",
    data: { labels, datasets: [{ label: "Touches", data: touches }] }
  });

  chartsContainer.classList.remove("hidden");
}
