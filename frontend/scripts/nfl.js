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
  QB: "🧢",       // helmet
  RB: "🏈",       // football
  WR: "👟",       // cleats
  TE: "👕"        // jersey
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

loadBtn.addEventListener("click", loadStats);
positionFilter.addEventListener("change", applyFilters);

document.querySelectorAll("#usage-table th").forEach(th => {
  th.addEventListener("click", () => {
    const column = th.dataset.sort;
    sortBy(column);
  });
});

compareSelect.addEventListener("change", renderCompare);

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
        efficiency: (player.total_yards ?? 0) / Math.max(player.touches ?? 1, 1),
        fantasy_per_touch: (player.fantasy_points_ppr ?? 0) / Math.max(player.touches ?? 1, 1)
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

function sortBy(column) {
  if (currentSort.column === column) {
    currentSort.direction *= -1;
  } else {
    currentSort.column = column;
    currentSort.direction = 1;
  }

  applyFilters();
}

function renderTable(data) {
  usageBody.innerHTML = data.map(player => {
    const color = teamColors[player.team] || "#444";
    const posIcon = positionIcons[player.position] || "";

    const logoUrl = `https://a.espncdn.com/i/teamlogos/nfl/500/${(player.team || "nfl").toLowerCase()}.png`;

    return `
      <tr>
        <td>${player.player_name}</td>
        <td>
          <span class="team-accent" style="background:${color}">
            <img class="team-logo" src="${logoUrl}" onerror="this.style.display='none';" />
            ${player.team}
          </span>
        </td>
        <td>${posIcon} ${player.position}</td>
        <td>${player.attempts ?? 0}</td>
        <td>${player.receptions ?? 0}</td>
        <td>${player.targets ?? 0}</td>
        <td>${player.passing_yards ?? 0}</td>
        <td>${player.rushing_yards ?? 0}</td>
        <td>${player.receiving_yards ?? 0}</td>
        <td>${player.total_yards ?? 0}</td>
        <td>${player.touches ?? 0}</td>
        <td>${player.snap_pct ? player.snap_pct.toFixed(1) : 0}</td>
        <td>${player.fantasy_points ?? 0}</td>
        <td>${player.fantasy_points_ppr ?? 0}</td>
        <td>${player.passing_epa?.toFixed(2) ?? 0}</td>
        <td>${player.rushing_epa?.toFixed(2) ?? 0}</td>
        <td>${player.receiving_epa?.toFixed(2) ?? 0}</td>
      </tr>
    `;
  }).join("");

  usageTable.classList.remove("hidden");
}

function renderCharts(data) {
  if (!touchesCanvas || !snapCanvas || !usageDonutCanvas) return;

  const labels = data.map(p => p.player_name);
  const touches = data.map(p => p.touches ?? 0);
  const snaps = data.map(p => p.snap_pct ?? 0);

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

  const totalPass = data.reduce((sum, p) => sum + (p.passing_yards ?? 0), 0);
  const totalRush = data.reduce((sum, p) => sum + (p.rushing_yards ?? 0), 0);
  const totalRec = data.reduce((sum, p) => sum + (p.receiving_yards ?? 0), 0);

  usageDonutChart = new Chart(usageDonutCanvas, {
    type: "doughnut",
    data: {
      labels: ["Passing Yards", "Rushing Yards", "Receiving Yards"],
      datasets: [{
        data: [totalPass, totalRush, totalRec],
        backgroundColor: ["#4ade80", "#60a5fa", "#f97316"]
      }]
    },
    options: {
      plugins: {
        legend: { labels: { color: "#d9eaff" } }
      }
    }
  });

  chartsContainer.classList.remove("hidden");
}

function renderTopPerformers(data) {
  const sortedByTouches = [...data].sort((a, b) => (b.touches ?? 0) - (a.touches ?? 0));
  const top = sortedByTouches.slice(0, 5);

  topList.innerHTML = top.map(p => {
    const posIcon = positionIcons[p.position] || "";
    return `
      <li>
        ${p.player_name} (${p.team}) ${posIcon}
        <span class="pill">Touches: ${p.touches ?? 0}</span>
        <span class="pill">Yds: ${p.total_yards ?? 0}</span>
        <span class="pill">Snap: ${p.snap_pct ? p.snap_pct.toFixed(1) : 0}%</span>
      </li>
    `;
  }).join("");

  topPanel.classList.remove("hidden");
}

function populateCompareSelect(data) {
  const sorted = [...data].sort((a, b) => (b.touches ?? 0) - (a.touches ?? 0));
  sorted.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.player_name;
    opt.textContent = `${p.player_name} (${p.team}, ${p.position})`;
    compareSelect.appendChild(opt);
  });

  comparePanel.classList.remove("hidden");
}

function renderCompare() {
  const selectedNames = Array.from(compareSelect.selectedOptions).map(o => o.value);
  const selectedPlayers = currentData.filter(p => selectedNames.includes(p.player_name));

  if (selectedPlayers.length === 0) {
    compareMetrics.innerHTML = "";
    return;
  }

  const lines = selectedPlayers.map(p => {
    return `
      <div>
        <strong>${p.player_name} (${p.team}, ${p.position})</strong><br/>
        Touches: ${p.touches ?? 0} |
        Total Yds: ${p.total_yards ?? 0} |
        Pass: ${p.passing_yards ?? 0} |
        Rush: ${p.rushing_yards ?? 0} |
        Rec: ${p.receiving_yards ?? 0} |
        Snap: ${p.snap_pct ? p.snap_pct.toFixed(1) : 0}%
      </div>
      <hr style="border-color:#1f2937;"/>
    `;
  }).join("");

  compareMetrics.innerHTML = lines;
}

