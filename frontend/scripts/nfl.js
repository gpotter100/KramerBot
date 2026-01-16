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
  QB: "🧢",  // helmet
  RB: "🏈",  // football
  WR: "👟",  // cleats
  TE: "👕"   // jersey
};

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
// Populate dropdowns dynamically
// ===============================
const currentYear = new Date().getFullYear();
const seasonOptions = [currentYear - 1, currentYear];
seasonInput.innerHTML = seasonOptions.map(y =>
  `<option value="${y}" ${y === currentYear ? "selected" : ""}>${y}</option>`
).join("");

weekInput.innerHTML = Array.from({ length: 18 }, (_, i) =>
  `<option value="${i + 1}">${i + 1}</option>`
).join("");

// ===============================
// Event bindings
// ===============================
loadBtn.addEventListener("click", loadStats);
positionFilter.addEventListener("change", applyFilters);

document.querySelectorAll("#usage-table th").forEach(th => {
  th.addEventListener("click", () => {
    const column = th.dataset.sort;
    sortBy(column);
  });
});

compareSelect.addEventListener("change", renderCompare);

// ===============================
// Load data
// ===============================
async function loadStats() {
  const season = Number(seasonInput.value);
  const week = Number(weekInput.value);

  if (season >= 2025) {
    alert("2025+ weekly data is not yet published by nflverse.");
    return;
  }

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

    currentData = data.map(p => ({
      ...p,
      touches: (p.attempts ?? 0) + (p.receptions ?? 0),
      total_yards:
        (p.passing_yards ?? 0) +
        (p.rushing_yards ?? 0) +
        (p.receiving_yards ?? 0),
      efficiency:
        ((p.passing_yards ?? 0) +
         (p.rushing_yards ?? 0) +
         (p.receiving_yards ?? 0)) / Math.max((p.attempts ?? 0) + (p.receptions ?? 0), 1),
      fantasy_per_touch:
        (p.fantasy_points_ppr ?? 0) / Math.max((p.attempts ?? 0) + (p.receptions ?? 0), 1)
    }));

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
// Filtering
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
// Sorting
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

