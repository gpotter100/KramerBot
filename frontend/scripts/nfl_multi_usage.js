import { API_BASE as BACKEND_URL } from "./config.js";

/* ==========================================================
   MULTI-WEEK USAGE + ATTRIBUTION
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

/* ===============================
   MULTI-SELECT WEEK HELPER
=============================== */
function getSelectedWeeks() {
  const selected = Array.from(weekInput.selectedOptions).map(o => o.value);

  if (selected.includes("ALL")) {
    return Array.from({ length: 18 }, (_, i) => i + 1);
  }

  return selected.map(Number);
}

/* ===============================
   NORMALIZATION
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

function normalizeRow(raw) {
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

  const fantasyPoints = num(raw.fantasy_points);
  const fantasyPointsPPR = num(raw.fantasy_points_ppr);
  const fantasyPointsHalf = num(raw.fantasy_points_half);
  const fantasyPointsShen = num(raw.fantasy_points_shen2000);

  return {
    ...raw,
    player_name: text(raw.player_name),
    team: text(raw.team),
    position: text(raw.position || raw.pos, "").toUpperCase(),

    attempts,
    receptions,
    targets,
    carries,
    passing_yards: passingYards,
    rushing_yards: rushingYards,
    receiving_yards: receivingYards,
    total_yards: totalYards,
    touchdowns,
    touches,

    fantasy_points: fantasyPoints,
    fantasy_points_ppr: fantasyPointsPPR,
    fantasy_points_half: fantasyPointsHalf,
    fantasy_points_shen2000: fantasyPointsShen
  };
}

/* ===============================
   SCORING FIELD
=============================== */
function scoringField() {
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
      return "fantasy_points";
    case "shen2000":
      return "fantasy_points_shen2000";
    default:
      return "fantasy_points";
  }
}

/* ===============================
   LOAD MULTI-WEEK DATA
=============================== */
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
    console.error("Error loading multi-week usage:", err);
    usageBody.innerHTML = `<tr><td colspan="15">Error loading data.</td></tr>`;
  } finally {
    loadingIndicator.classList.add("hidden");
    tableWrapper.classList.remove("hidden");
  }
}

/* ===============================
   TABLE RENDERING
=============================== */
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

/* ===============================
   EVENT BINDINGS
=============================== */
loadBtn?.addEventListener("click", loadMultiUsage);
