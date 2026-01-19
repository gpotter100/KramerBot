import { API_BASE as BACKEND_URL } from "./config.js";

/* ==========================================================
   MULTI-WEEK USAGE + ATTRIBUTION (UPGRADED)
   - Loads seasons dynamically
   - Loads week options dynamically
   - Multi-select week filter
   - Aggregates usage across weeks
   - Schema-tolerant normalization
   - Supports scoring system selection
========================================================== */

let multiData = [];
let currentSort = { column: null, direction: 1 };

/* ===============================
   DOM ELEMENTS
=============================== */
const seasonInput = document.getElementById("multi-season-input");
const weekInput = document.getElementById("multi-week-input");
const scoringFilter = document.getElementById("multi-scoring-filter");
const loadBtn = document.getElementById("multi-load-btn");

const tableWrapper = document.getElementById("multi-table-wrapper");
const usageBody = document.getElementById("multi-usage-body");
const loadingIndicator = document.getElementById("multi-loading-indicator");

/* ==========================================================
   LOAD SEASONS (NEW)
========================================================== */
async function loadSeasons() {
  try {
    const res = await fetch(`${BACKEND_URL}/nfl/seasons`);
    const seasons = await res.json();

    console.log("SEASONS FETCHED (multi-week):", seasons);

    if (!seasonInput) {
      console.error("❌ multi-season-input element missing");
      return;
    }

    seasonInput.innerHTML = "";

    seasons.forEach(season => {
      const opt = document.createElement("option");
      opt.value = season;
      opt.textContent = season;
      seasonInput.appendChild(opt);
    });

    // Auto-select latest season
    if (seasons.length) {
      seasonInput.value = seasons[seasons.length - 1];
    }

  } catch (err) {
    console.error("❌ Failed to load seasons:", err);
  }
}

/* ==========================================================
   LOAD WEEK OPTIONS (NEW)
========================================================== */
function loadWeekOptions() {
  if (!weekInput) {
    console.error("❌ multi-week-input element missing");
    return;
  }

  weekInput.innerHTML = "";

  // ALL option
  const allOpt = document.createElement("option");
  allOpt.value = "ALL";
  allOpt.textContent = "ALL Weeks";
  weekInput.appendChild(allOpt);

  // Weeks 1–18
  for (let w = 1; w <= 18; w++) {
    const opt = document.createElement("option");
    opt.value = w;
    opt.textContent = `Week ${w}`;
    weekInput.appendChild(opt);
  }
}

/* ==========================================================
   MULTI-SELECT WEEK HELPER
========================================================== */
function getSelectedWeeks() {
  const selected = Array.from(weekInput.selectedOptions).map(o => o.value);

  if (selected.includes("ALL")) {
    return Array.from({ length: 18 }, (_, i) => i + 1);
  }

  return selected.map(Number);
}

/* ==========================================================
   NORMALIZATION
========================================================== */
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

function normalizeRow(raw) {
  const attempts = num(raw.attempts);
  const receptions = num(raw.receptions);

  const passingYards = num(raw.passing_yards);
  const rushingYards = num(raw.rushing_yards);
  const receivingYards = num(raw.receiving_yards);

  const passingTDs = num(raw.passing_tds);
  const rushingTDs = num(raw.rushing_tds);
  const receivingTDs = num(raw.receiving_tds);

  return {
    ...raw,
    player_name: text(raw.player_name),
    team: text(raw.team),
    position: text(raw.position || raw.pos, "").toUpperCase(),

    attempts,
    receptions,
    passing_yards: passingYards,
    rushing_yards: rushingYards,
    receiving_yards: receivingYards,

    total_yards: passingYards + rushingYards + receivingYards,
    touchdowns: passingTDs + rushingTDs + receivingTDs,
    touches: attempts + receptions,

    fantasy_points: num(raw.fantasy_points),
    fantasy_points_ppr: num(raw.fantasy_points_ppr),
    fantasy_points_half: num(raw.fantasy_points_half),
    fantasy_points_shen2000: num(raw.fantasy_points_shen2000)
  };
}

/* ==========================================================
   SCORING FIELD
========================================================== */
function scoringField() {
  const scoring = (scoringFilter?.value || "standard").toLowerCase();

  switch (scoring) {
    case "standard":
      return "fantasy_points";
    case "ppr":
      return "fantasy_points_ppr";
    case "half-ppr":
    case "half_ppr":
    case "half":
      return "fantasy_points_half";
    case "vandalay":
      return "fantasy_points";
    case "shen2000":
      return "fantasy_points_shen2000";
    default:
      return "fantasy_points";
  }
}

/* ==========================================================
   LOAD MULTI-WEEK DATA
========================================================== */
async function loadMultiUsage() {
  const season = Number(seasonInput.value);
  const weeks = getSelectedWeeks();
  const scoring = scoringFilter.value;

  const weekParam = weeks.join(",");

  usageBody.innerHTML = "";
  tableWrapper.classList.add("hidden");
  loadingIndicator.classList.remove("hidden");

  try {
    const res = await fetch(
      `${BACKEND_URL}/nfl/multi-usage/${season}?weeks=${weekParam}&scoring=${encodeURIComponent(scoring)}`
    );

    if (!res.ok) throw new Error(`Backend returned ${res.status}`);

    const payload = await res.json();
    const rows = Array.isArray(payload) ? payload : [];

    multiData = rows.map(normalizeRow);

    renderTable(multiData);
  } catch (err) {
    console.error("❌ Error loading multi-week usage:", err);
    usageBody.innerHTML = `<tr><td colspan="15">Error loading data.</td></tr>`;
  } finally {
    loadingIndicator.classList.add("hidden");
    tableWrapper.classList.remove("hidden");
  }
}

/* ==========================================================
   TABLE RENDERING
========================================================== */
function renderTable(data) {
  if (!data.length) {
    usageBody.innerHTML = `<tr><td colspan="15">No data returned.</td></tr>`;
    return;
  }

  const field = scoringField();

  usageBody.innerHTML = data
    .map(p => `
      <tr>
        <td>${text(p.player_name)}</td>
        <td>${text(p.team)}</td>
        <td>${text(p.position)}</td>
        <td>${num(p.touches)}</td>
        <td>${num(p.total_yards)}</td>
        <td>${num(p.touchdowns)}</td>
        <td>${num(p[field]).toFixed(1)}</td>
      </tr>
    `)
    .join("");
}

/* ==========================================================
   INIT (NEW)
========================================================== */
document.addEventListener("DOMContentLoaded", () => {
  loadSeasons();
  loadWeekOptions();
});

/* ==========================================================
   EVENT BINDINGS
========================================================== */
loadBtn?.addEventListener("click", loadMultiUsage);
