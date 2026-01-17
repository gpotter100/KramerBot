import { API_BASE as BACKEND_URL } from "./config.js";

/* ==========================================================
   NFL PAGE — PRODUCTION nfl.js
   Goals:
   - Be schema-tolerant (backend drift won’t blank the UI)
   - Derive missing fields deterministically (half-PPR, TDs, totals)
   - Never call .toFixed() on undefined
   - Render table + top performers + charts reliably
========================================================== */

let currentData = [];
let currentSort = { column: null, direction: 1 };

const positionIcons = { QB: "🧢", RB: "🏈", WR: "👟", TE: "👕" };

/* ===============================
   DOM ELEMENTS
=============================== */
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

/* ===============================
   HELPERS (safe + formatting)
=============================== */
function num(v) {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
  return 0;
}

function text(v, fallback = "—") {
  if (v === undefined || v === null) return fallback;
  const s = String(v);
  return s.trim() === "" ? fallback : s;
}

function fmtInt(v) {
  return String(Math.round(num(v)));
}

function fmt1(v) {
  return num(v).toFixed(1);
}

function fmt2(v) {
  return num(v).toFixed(2);
}

function setHidden(el, hidden) {
  if (!el) return;
  el.classList.toggle("hidden", hidden);
}

function normalizePlayer(raw) {
  // Core inputs (whatever backend gives us)
  const attempts = num(raw.attempts);           // passing attempts (QB)
  const receptions = num(raw.receptions);
  const targets = num(raw.targets);
  const carries = num(raw.carries);             // rushing attempts (RB/WR/QB)
  const passingYards = num(raw.passing_yards);
  const rushingYards = num(raw.rushing_yards);
  const receivingYards = num(raw.receiving_yards);
  const passingTDs = num(raw.passing_tds);
  const rushingTDs = num(raw.rushing_tds);
  const receivingTDs = num(raw.receiving_tds);

  // Derived outputs (deterministic)
  const totalYards = passingYards + rushingYards + receivingYards;

  // Touches in your UI historically = attempts + receptions (keep this, even if imperfect)
  const touches = attempts + receptions;

  const touchdowns = passingTDs + rushingTDs + receivingTDs;

  const fantasyPoints = num(raw.fantasy_points);
  const fantasyPointsPPR = num(raw.fantasy_points_ppr);

  // If backend doesn't provide half PPR, derive it.
  // If backend does provide it in the future, prefer backend value.
  const fantasyPointsHalf = raw.fantasy_points_half !== undefined
    ? num(raw.fantasy_points_half)
    : (fantasyPoints + 0.5 * receptions);

  const efficiency = touches > 0 ? totalYards / touches : 0;
  const fantasyPerTouch = touches > 0 ? fantasyPointsPPR / touches : 0;

  return {
    ...raw,

    // normalized strings
    player_name: text(raw.player_name),
    position: text(raw.position, "").toUpperCase(),
    team: text(raw.team, text(raw.recent_team, "")), // tolerate alt keys

    // core numeric fields (ensures numbers)
    attempts,
    receptions,
    targets,
    carries,
    passing_yards: passingYards,
    rushing_yards: rushingYards,
    receiving_yards: receivingYards,
    passing_tds: passingTDs,
    rushing_tds: rushingTDs,
    receiving_tds: receivingTDs,

    // derived fields used by UI
    total_yards: totalYards,
    touches,
    touchdowns,
    fantasy_points: fantasyPoints,
    fantasy_points_ppr: fantasyPointsPPR,
    fantasy_points_half: fantasyPointsHalf,
    efficiency,
    fantasy_per_touch: fantasyPerTouch,

    // optional chart input
    snap_pct: num(raw.snap_pct),
  };
}

function safeSortValue(v) {
  // sort numbers numerically when possible, otherwise strings
  if (typeof v === "number") return v;
  if (typeof v === "string") return v.toLowerCase();
  return v ?? 0;
}

/* ===============================
   INIT DROPDOWNS
=============================== */
async function initDropdowns() {
  try {
    const res = await fetch(`${BACKEND_URL}/nfl/seasons`);
    if (!res.ok) throw new Error(`Seasons endpoint returned ${res.status}`);
    const seasons = await res.json();

    seasonInput.innerHTML = (Array.isArray(seasons) ? seasons : [])
      .sort((a, b) => b - a)
      .map(y => `<option value="${y}">${y}</option>`)
      .join("");

    weekInput.innerHTML = Array.from({ length: 18 }, (_, i) =>
      `<option value="${i + 1}">${i + 1}</option>`
    ).join("");
  } catch (err) {
    console.error("Failed to load seasons:", err);
    seasonInput.innerHTML = `<option value="2024">2024</option>`;
    weekInput.innerHTML = Array.from({ length: 18 }, (_, i) =>
      `<option value="${i + 1}">${i + 1}</option>`
    ).join("");
  }
}

initDropdowns();

/* ===============================
   EVENT BINDINGS
=============================== */
loadBtn?.addEventListener("click", loadStats);
positionFilter?.addEventListener("change", applyFilters);

document.querySelectorAll("#usage-table th").forEach(th => {
  th.addEventListener("click", () => {
    const col = th.dataset.sort;
    if (!col) return;
    sortBy(col);
  });
});

compareSelect?.addEventListener("change", renderCompare);

/* ===============================
   LOAD DATA
=============================== */
async function loadStats() {
  const season = Number(seasonInput?.value);
  const week = Number(weekInput?.value);

  // Reset UI
  setHidden(usageTable, true);
  setHidden(chartsContainer, true);
  setHidden(topPanel, true);
  setHidden(comparePanel, true);
  setHidden(loadingIndicator, false);

  usageBody.innerHTML = "";
  topList.innerHTML = "";
  compareSelect.innerHTML = "";
  compareMetrics.innerHTML = "";

  try {
    const res = await fetch(`${BACKEND_URL}/nfl/player-usage/${season}/${week}`);
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);

    const payload = await res.json();
    const rows = Array.isArray(payload) ? payload : [];

    if (!rows.length) {
      usageBody.innerHTML = `<tr><td colspan="15">No data returned for this week.</td></tr>`;
      setHidden(usageTable, false);
      return;
    }

    // Normalize + derive fields
    currentData = rows.map(normalizePlayer);

    // Populate UI
    populateCompareSelect(currentData);
    applyFilters();
    renderTopPerformers(currentData);
  } catch (err) {
    console.error("Error loading NFL data:", err);
    usageBody.innerHTML = `<tr><td colspan="15">Error loading data.</td></tr>`;
    setHidden(usageTable, false);
  } finally {
    setHidden(loadingIndicator, true);
  }
}

/* ===============================
   FILTERING
=============================== */
function applyFilters() {
  let filtered = [...currentData];

  const pos = (positionFilter?.value || "ALL").toUpperCase();
  if (pos !== "ALL") {
    filtered = filtered.filter(p => (p.position || "").toUpperCase() === pos);
  }

  if (currentSort.column) {
    const col = currentSort.column;
    const dir = currentSort.direction;

    filtered.sort((a, b) => {
      const va = safeSortValue(a[col]);
      const vb = safeSortValue(b[col]);

      if (typeof va === "number" && typeof vb === "number") return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
  }

  renderTable(filtered);
  renderCharts(filtered);
}

/* ===============================
   SORTING
=============================== */
function sortBy(column) {
  if (currentSort.column === column) {
    currentSort.direction *= -1;
  } else {
    currentSort.column = column;
    currentSort.direction = 1;
  }
  applyFilters();
}

/* ===============================
   TABLE RENDERING
=============================== */
function renderTable(data) {
  if (!Array.isArray(data) || data.length === 0) {
    usageBody.innerHTML = `<tr><td colspan="15">No players match your filters.</td></tr>`;
    setHidden(usageTable, false);
    return;
  }

  usageBody.innerHTML = data.map(p => `
    <tr>
      <td>${positionIcons[p.position] || text(p.position, "")}</td>
      <td>${text(p.player_name)}</td>
      <td>${text(p.team)}</td>
      <td>${fmtInt(p.attempts)}</td>
      <td>${fmtInt(p.receptions)}</td>
      <td>${fmtInt(p.targets)}</td>
      <td>${fmtInt(p.carries)}</td>
      <td>${fmtInt(p.total_yards)}</td>
      <td>${fmtInt(p.touchdowns)}</td>
      <td>${fmt1(p.fantasy_points)}</td>
      <td>${fmt1(p.fantasy_points_half)}</td>
      <td>${fmt1(p.fantasy_points_ppr)}</td>
      <td>${fmtInt(p.touches)}</td>
      <td>${fmt2(p.efficiency)}</td>
      <td>${fmt2(p.fantasy_per_touch)}</td>
    </tr>
  `).join("");

  setHidden(usageTable, false);
}

/* ===============================
   TOP PERFORMERS
=============================== */
function renderTopPerformers(data) {
  const top = [...data]
    .sort((a, b) => num(b.fantasy_points_ppr) - num(a.fantasy_points_ppr))
    .slice(0, 10);

  topList.innerHTML = top.map(p => `
    <li>
      ${positionIcons[p.position] || ""}
      <strong>${text(p.player_name)}</strong> — ${fmt1(p.fantasy_points_ppr)} pts
    </li>
  `).join("");

  setHidden(topPanel, false);
}

/* ===============================
   COMPARE PANEL
=============================== */
function populateCompareSelect(data) {
  // Use stable identity even when names collide
  // If backend later provides a player_id, we can switch to that.
  compareSelect.innerHTML = data
    .map((p, idx) => {
      const label = `${text(p.player_name)}${p.team ? ` (${p.team})` : ""}`;
      return `<option value="${idx}">${label}</option>`;
    })
    .join("");

  setHidden(comparePanel, false);

  // Render first by default
  if (data.length) {
    compareSelect.value = "0";
    renderCompare();
  }
}

function renderCompare() {
  const idx = Number(compareSelect.value);
  const player = currentData[idx];
  if (!player) return;

  compareMetrics.innerHTML = `
    <p><strong>${text(player.player_name)}</strong>${player.team ? ` — ${text(player.team)}` : ""}</p>
    <p>Pos: ${text(player.position, "—")}</p>
    <p>Touches: ${fmtInt(player.touches)}</p>
    <p>Total Yards: ${fmtInt(player.total_yards)}</p>
    <p>TDs: ${fmtInt(player.touchdowns)}</p>
    <p>Fantasy (PPR): ${fmt1(player.fantasy_points_ppr)}</p>
    <p>Fantasy (Half): ${fmt1(player.fantasy_points_half)}</p>
    <p>Efficiency (yds/touch): ${fmt2(player.efficiency)}</p>
  `;
}

/* ===============================
   CHARTS
=============================== */
function renderCharts(data) {
  if (!Array.isArray(data) || data.length === 0) return;

  // Limit chart density to keep canvas readable
  const chartData = [...data]
    .sort((a, b) => num(b.touches) - num(a.touches))
    .slice(0, 25);

  const labels = chartData.map(p => text(p.player_name));
  const touches = chartData.map(p => num(p.touches));
  const snapPct = chartData.map(p => num(p.snap_pct));

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
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { display: false } },
        y: { beginAtZero: true }
      }
    }
  });

  snapChart = new Chart(snapCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Snap %",
        data: snapPct,
        borderColor: "#e15759",
        backgroundColor: "rgba(225,87,89,0.15)",
        fill: true,
        tension: 0.25,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { display: false } },
        y: { beginAtZero: true, max: 100 }
      }
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
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom" } }
    }
  });

  setHidden(chartsContainer, false);
}
