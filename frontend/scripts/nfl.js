// ===============================
// CONFIG
// ===============================

const backendBase = "https://kramerbot-backend.onrender.com";

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
let touchesChart, snapChart;

// ===============================
// LOAD DATA
// ===============================

loadBtn.addEventListener("click", loadStats);

async function loadStats() {
  const season = seasonInput.value;
  const week = weekInput.value;

  usageTable.classList.add("hidden");
  chartsContainer.classList.add("hidden");
  loadingIndicator.classList.remove("hidden");

  try {
    const res = await fetch(`${backendBase}/nfl/player-usage/${season}/${week}`);
    const data = await res.json();

    currentData = data;
    applyFilters();
  } catch (err) {
    usageBody.innerHTML = `<tr><td colspan="7">Error loading data.</td></tr>`;
  }

  loadingIndicator.classList.add("hidden");
}

// ===============================
// FILTERING
// ===============================

positionFilter.addEventListener("change", applyFilters);

function applyFilters() {
  let filtered = [...currentData];

  if (positionFilter.value !== "ALL") {
    filtered = filtered.filter(p => p.position === positionFilter.value);
  }

  renderTable(filtered);
  renderCharts(filtered);
}

// ===============================
// SORTING
// ===============================

document.querySelectorAll("#usage-table th").forEach(th => {
  th.addEventListener("click", () => {
    const column = th.dataset.sort;
    sortBy(column);
  });
});

function sortBy(column) {
  if (currentSort.column === column) {
    currentSort.direction *= -1;
  } else {
    currentSort.column = column;
    currentSort.direction = 1;
  }

  const sorted = [...currentData].sort((a, b) => {
    const valA = a[column] ?? 0;
    const valB = b[column] ?? 0;
    return (valA > valB ? 1 : -1) * currentSort.direction;
  });

  renderTable(sorted);
  renderCharts(sorted);
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
  const labels = data.map(p => p.player_name);
  const touches = data.map(p => (p.attempts ?? 0) + (p.receptions ?? 0));
  const snaps = data.map(p => p.snap_pct ?? 0);

  if (touchesChart) touchesChart.destroy();
  if (snapChart) snapChart.destroy();

  touchesChart = new Chart(document.getElementById("touches-chart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Touches",
        data: touches,
        backgroundColor: "#66ccff"
      }]
    }
  });

  snapChart = new Chart(document.getElementById("snap-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Snap %",
        data: snaps,
        borderColor: "#66ccff",
        backgroundColor: "rgba(102, 204, 255, 0.2)"
      }]
    }
  });

  chartsContainer.classList.remove("hidden");
}
