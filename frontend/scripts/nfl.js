import { API_BASE as BACKEND_URL } from "./config.js";

function buildFantasyBreakdown(p) {
  const safe = v => (typeof v === "number" ? v : 0);

  return {
    passing: {
      yds: safe(p.passing_yards),
      fpts_yds: safe(p.comp_passing_yards),
      attr_pct_yds: safe(p.pct_passing_yards),
      tds: safe(p.passing_tds),
      fpts_tds: safe(p.comp_passing_tds),
      attr_pct_tds: safe(p.pct_passing_tds),
      int: safe(p.interceptions),
      fpts_int: safe(p.comp_interceptions),
      attr_pct_int: safe(p.pct_interceptions),
    },
    rushing: {
      yds: safe(p.rushing_yards),
      fpts_yds: safe(p.comp_rushing_yards),
      attr_pct_yds: safe(p.pct_rushing_yards),
      tds: safe(p.rushing_tds),
      fpts_tds: safe(p.comp_rushing_tds),
      attr_pct_tds: safe(p.pct_rushing_tds),
    },
    receiving: {
      rec: safe(p.receptions),
      fpts_rec: safe(p.comp_receptions),
      attr_pct_rec: safe(p.pct_receptions),
      yds: safe(p.receiving_yards),
      fpts_yds: safe(p.comp_receiving_yards),
      attr_pct_yds: safe(p.pct_receiving_yards),
      tds: safe(p.receiving_tds),
      fpts_tds: safe(p.comp_receiving_tds),
      attr_pct_tds: safe(p.pct_receiving_tds),
    },
    fumbles: {
      lost: safe(p.fumbles_lost),
      fpts_lost: safe(p.comp_fumbles_lost),
      attr_pct_lost: safe(p.pct_fumbles_lost),
    },
    fantasy: {
      total: safe(p.fantasy_points),
    },
  };
}


/* ==========================================================
   NFL PAGE — PRODUCTION nfl.js
   Goals:
   - Be schema-tolerant (backend drift won’t blank the UI)
   - Derive missing fields deterministically (half-PPR, TDs, totals)
   - Never call .toFixed() on undefined
   - Render table + top performers + charts reliably
   - Support selectable scoring systems
========================================================== */

let currentData = [];
let currentSort = { column: null, direction: 1 };

const positionIcons = { QB: "🧢", RB: "🏈", WR: "👟", TE: "👕" };

/* ===============================
   DOM ELEMENTS
=============================== */
const seasonInput = document.getElementById("season-input");
const multiSeasonInput = document.getElementById("multi-season-input");
const multiPbpSeasonInput = document.getElementById("pbp-multi-season-input");
const weekInput = document.getElementById("week-input");
const multiWeekInput = document.getElementById("multi-week-input");
const pbpMultiWeekInput = document.getElementById("pbp-multi-week-input");
const positionFilter = document.getElementById("position-filter");
const scoringFilter = document.getElementById("scoring-filter");
const loadBtn = document.getElementById("load-btn");

const loadingIndicator = document.getElementById("loading-indicator");
const tableWrapper = document.getElementById("table-wrapper");
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

/* ===============================
   HELPERS (safe + formatting)
=============================== */
function num(v) {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
  return 0;
}

function isFiniteNumber(v) {
  return typeof v === "number" && Number.isFinite(v);
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

function scoringFieldForCurrentSelection() {
  const scoring = (scoringFilter?.value || "standard").toLowerCase();

  switch (scoring) {
    case "standard":
      return "fantasy_points";
    case "ppr":
      return "fantasy_points_ppr";
    case "half-ppr":
    case "half_ppr":
      return "fantasy_points_half";
    case "vandalay":
      return "fantasy_points_vandalay";            // Vandalay uses the base field
    case "shen2000":
    case "shen 2000":
      return "fantasy_points_shen2000";   // SHEN 2000 backend field
    default:
      return "fantasy_points_ppr";
  }
}

function normalizePlayer(raw) {
  const attempts = num(raw.attempts);
  const receptions = num(raw.receptions);
  const targets = num(raw.targets);
  const carries = num(raw.carries);
  const passingYards = num(raw.passing_yards);
  const rushingYards = num(raw.rushing_yards);
  const receivingYards = num(raw.receiving_yards);
  const passingTDs = num(raw.passing_tds);
  const rushingTDs = num(raw.rushing_tds);
  const receivingTDs = num(raw.receiving_tds);

  const totalYards = passingYards + rushingYards + receivingYards;
  const touches = attempts + receptions;
  const touchdowns = passingTDs + rushingTDs + receivingTDs;

  // Backend now ALWAYS provides fantasy_points for Vandalay
  const fantasyPoints = num(raw.fantasy_points_vandalay);   // Vandalay uses the base field

  // SHEN 2000 backend field
  const shen2000Points = num(raw.fantasy_points_shen2000);

  const fantasyPointsPPR = isFiniteNumber(raw.fantasy_points_ppr)
    ? num(raw.fantasy_points_ppr)
    : (fantasyPoints + receptions);

  const fantasyPointsHalf = isFiniteNumber(raw.fantasy_points_half)
    ? num(raw.fantasy_points_half)
    : (fantasyPoints + 0.5 * receptions);

  const efficiency = touches > 0 ? totalYards / touches : 0;
  const fantasyPerTouch = touches > 0 ? fantasyPointsPPR / touches : 0;


  return {
    ...raw,
    player_name: text(raw.player_name),
    position: text(raw.position || raw.pos, "").toUpperCase(),
    team: text(raw.team, text(raw.recent_team, "")),

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

    total_yards: totalYards,
    touches,
    touchdowns,
    fantasy_points: fantasyPoints,
    fantasy_points_ppr: fantasyPointsPPR,
    fantasy_points_half: fantasyPointsHalf,
    efficiency,
    fantasy_per_touch: fantasyPerTouch,

    snap_pct: num(raw.snap_pct),
  };
}

function safeSortValue(v) {
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

/* ==========================================================
   INIT (NEW)
========================================================== */
document.addEventListener("DOMContentLoaded", () => {
  initDropdowns();
});



/* ===============================
   EVENT BINDINGS
=============================== */
loadBtn?.addEventListener("click", loadStats);
positionFilter?.addEventListener("change", applyFilters);
scoringFilter?.addEventListener("change", applyFilters);

document.querySelectorAll("#usage-table th").forEach(th => {
  th.addEventListener("click", () => {
    let col = th.dataset.sort;
    if (!col) return;

    // If sorting by fantasy, map to current scoring field
    if (col === "fantasy_points") {
      col = scoringFieldForCurrentSelection();
    }

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
  const scoring = scoringFilter?.value || "standard";

  setHidden(tableWrapper, false);
  setHidden(chartsContainer, true);
  setHidden(topPanel, true);
  setHidden(comparePanel, true);
  setHidden(loadingIndicator, false);

  usageBody.innerHTML = "";
  topList.innerHTML = "";
  compareSelect.innerHTML = "";
  compareMetrics.innerHTML = "";

  try {
    const res = await fetch(
      `${BACKEND_URL}/nfl/player-usage/${season}/${week}?scoring=${encodeURIComponent(scoring)}`
    );
    if (!res.ok) throw new Error(`Backend returned ${res.status}`);

    const payload = await res.json();
    const rows = Array.isArray(payload) ? payload : [];

    if (!rows.length) {
      usageBody.innerHTML = `<tr><td colspan="15">No data returned for this week.</td></tr>`;
      setHidden(tableWrapper, false);
      return;
    }

    currentData = rows.map(normalizePlayer);
    console.log("Row keys:", Object.keys(rows[0]));


    populateCompareSelect(currentData);
    applyFilters();
  } catch (err) {
    console.error("Error loading NFL data:", err);
    usageBody.innerHTML = `<tr><td colspan="15">Error loading data.</td></tr>`;
    setHidden(tableWrapper, false);
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
  renderTopPerformers(filtered);
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
  const scoringField = scoringFieldForCurrentSelection();

  // STEP 3A — use breakdown inside the row template
  usageBody.innerHTML = data.map((p, idx) => {
    const breakdown = buildFantasyBreakdown(p);

    return `
      <tr data-player-id="${p.player_id}">
        <td>${positionIcons[p.position] || text(p.position, "")}</td>
        <td>${text(p.player_name)}</td>
        <td>${text(p.team)}</td>

        <!-- Example: show passing yards -->
        <td>${fmtInt(breakdown.passing.yds)}</td>

        <!-- Example: show fantasy points from passing yards -->
        <td>${fmt1(breakdown.passing.fpts_yds)}</td>

        <!-- Example: show attribution % -->
        <td>${fmt1(breakdown.passing.attr_pct_yds)}%</td>

        <!-- Example: total fantasy -->
        <td>${fmt1(breakdown.fantasy.total)}</td>
      </tr>
    `;
  }).join("");

  // STEP 3B — attach click handlers to each row
  document.querySelectorAll("#usage-body tr").forEach(row => {
    row.addEventListener("click", () => {
      const playerId = row.dataset.playerId;
      const player = data.find(p => p.player_id === playerId);
      renderPlayerBreakdown(player);
    });
  });

  setHidden(tableWrapper, false);
}


function renderPlayerBreakdown(player) {
  const panel = document.getElementById("player-breakdown-panel");
  if (!panel) return;

  const b = buildFantasyBreakdown(player);

  panel.innerHTML = `
    <div class="breakdown-header">
      <h2>${text(player.player_name)} — ${text(player.team)}</h2>
      <p>Position: ${text(player.position)}</p>
      <p>Total Fantasy: ${fmt1(b.fantasy.total)}</p>
    </div>

    <div class="breakdown-section">
      <h3>Passing</h3>
      <p>Yards: ${b.passing.yds}</p>
      <p>Fantasy from Yards: ${fmt1(b.passing.fpts_yds)}</p>
      <p>Attribution % (Yards): ${fmt1(b.passing.attr_pct_yds)}%</p>
      <p>TDs: ${b.passing.tds}</p>
      <p>Fantasy from TDs: ${fmt1(b.passing.fpts_tds)}</p>
      <p>Attribution % (TDs): ${fmt1(b.passing.attr_pct_tds)}%</p>
      <p>Interceptions: ${b.passing.int}</p>
      <p>Fantasy from INTs: ${fmt1(b.passing.fpts_int)}</p>
      <p>Attribution % (INTs): ${fmt1(b.passing.attr_pct_int)}%</p>
    </div>

    <div class="breakdown-section">
      <h3>Rushing</h3>
      <p>Yards: ${b.rushing.yds}</p>
      <p>Fantasy from Yards: ${fmt1(b.rushing.fpts_yds)}</p>
      <p>Attribution % (Yards): ${fmt1(b.rushing.attr_pct_yds)}%</p>
      <p>TDs: ${b.rushing.tds}</p>
      <p>Fantasy from TDs: ${fmt1(b.rushing.fpts_tds)}</p>
      <p>Attribution % (TDs): ${fmt1(b.rushing.attr_pct_tds)}%</p>
    </div>

    <div class="breakdown-section">
      <h3>Receiving</h3>
      <p>Receptions: ${b.receiving.rec}</p>
      <p>Fantasy from Receptions: ${fmt1(b.receiving.fpts_rec)}</p>
      <p>Attribution % (Receptions): ${fmt1(b.receiving.attr_pct_rec)}%</p>
      <p>Yards: ${b.receiving.yds}</p>
      <p>Fantasy from Yards: ${fmt1(b.receiving.fpts_yds)}</p>
      <p>Attribution % (Yards): ${fmt1(b.receiving.attr_pct_yds)}%</p>
      <p>TDs: ${b.receiving.tds}</p>
      <p>Fantasy from TDs: ${fmt1(b.receiving.fpts_tds)}</p>
      <p>Attribution % (TDs): ${fmt1(b.receiving.attr_pct_tds)}%</p>
    </div>

    <div class="breakdown-section">
      <h3>Fumbles</h3>
      <p>Lost: ${b.fumbles.lost}</p>
      <p>Fantasy from Fumbles: ${fmt1(b.fumbles.fpts_lost)}</p>
      <p>Attribution %: ${fmt1(b.fumbles.attr_pct_lost)}%</p>
    </div>
  `;

  panel.classList.remove("hidden");
}


/* ===============================
   TOP PERFORMERS
=============================== */
function renderTopPerformers(data) {
  if (!Array.isArray(data) || data.length === 0) {
    topList.innerHTML = "";
    setHidden(topPanel, true);
    return;
  }

  const field = scoringFieldForCurrentSelection();

  const top = [...data]
    .sort((a, b) => num(b[field]) - num(a[field]))
    .slice(0, 10);

  topList.innerHTML = top.map(p => `
    <li>
      ${positionIcons[p.position] || ""}
      <strong>${text(p.player_name)}</strong> — ${fmt1(p[field])} pts
    </li>
  `).join("");

  setHidden(topPanel, false);
}
/* ===============================
   Attribution Breakdown
=============================== */



/* ===============================
   COMPARE PANEL
=============================== */
function populateCompareSelect(data) {
  compareSelect.innerHTML = data
    .map((p, idx) => {
      const label = `${text(p.player_name)}${p.team ? ` (${p.team})` : ""}`;
      return `<option value="${idx}">${label}</option>`;
    })
    .join("");

  setHidden(comparePanel, false);

  if (data.length) {
    compareSelect.value = "0";
    renderCompare();
  }
}

function renderCompare() {
  const idx = Number(compareSelect.value);
  const player = currentData[idx];
  if (!player) return;

  const field = scoringFieldForCurrentSelection();

  compareMetrics.innerHTML = `
    <p><strong>${text(player.player_name)}</strong>${player.team ? ` — ${text(player.team)}` : ""}</p>
    <p>Pos: ${text(player.position, "—")}</p>
    <p>Touches: ${fmtInt(player.touches)}</p>
    <p>Total Yards: ${fmtInt(player.total_yards)}</p>
    <p>TDs: ${fmtInt(player.touchdowns)}</p>
    <p>Fantasy (${text(scoringFilter?.value || "Standard")}): ${fmt1(player[field])}</p>
    <p>Efficiency (yds/touch): ${fmt2(player.efficiency)}</p>
  `;
}

/* ===============================
   CHARTS
=============================== */

function renderCharts(data) {
  if (!Array.isArray(data) || data.length === 0) return;

  const chartData = [...data]
    .sort((a, b) => num(b.touches) - num(a.touches))
    .slice(0, 25);

  const labels = chartData.map(p => text(p.player_name));
  const touches = chartData.map(p => num(p.touches));
  const snapPct = chartData.map(p => num(p.snap_pct));

  // Destroy existing charts safely
  if (touchesChart) {
    touchesChart.destroy();
    touchesChart = null;
  }
  if (snapChart) {
    snapChart.destroy();
    snapChart = null;
  }
  

  // Render touches bar chart
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

  // Render snap % line chart
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


  setHidden(chartsContainer, false);
}

/* ============================================================
   SIDEBAR DROPDOWN TOGGLE
============================================================ */
document.querySelectorAll(".sidebar-dropdown .dropdown-toggle").forEach(btn => {
  btn.addEventListener("click", () => {
    const menu = btn.nextElementSibling;
    if (menu) {
      menu.style.display = menu.style.display === "flex" ? "none" : "flex";
    }
  });
});

