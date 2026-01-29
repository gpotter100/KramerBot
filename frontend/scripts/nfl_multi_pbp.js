import { API_BASE as BACKEND_URL } from "./config.js";

/* ==========================================================
   MULTI-WEEK PBP EXPLORER (UPGRADED + FIXED)
========================================================== */

let pbpData = [];

/* ===============================
   DOM ELEMENTS (FIXED IDS)
=============================== */
const seasonInput = document.getElementById("pbp-season-input");
const weekInput = document.getElementById("pbp-week-input");
const loadBtn = document.getElementById("pbp-load-btn");

const tableWrapper = document.getElementById("pbp-table-wrapper");
const pbpBody = document.getElementById("pbp-body");
const loadingIndicator = document.getElementById("pbp-loading");   // FIXED
const chartsContainer = document.getElementById("pbp-charts");      // OPTIONAL CHARTS

/* ==========================================================
   LOAD SEASONS
========================================================== */
async function loadSeasons() {
  try {
    const res = await fetch(`${BACKEND_URL}/nfl/seasons`);
    const seasons = await res.json();

    console.log("SEASONS FETCHED (PBP):", seasons);

    if (!seasonInput) {
      console.error("❌ pbp-season-input element missing");
      return;
    }

    seasonInput.innerHTML = "";

    seasons.forEach(season => {
      const opt = document.createElement("option");
      opt.value = season;
      opt.textContent = season;
      seasonInput.appendChild(opt);
    });

    if (seasons.length) {
      seasonInput.value = seasons[seasons.length - 1];
    }

  } catch (err) {
    console.error("❌ Failed to load PBP seasons:", err);
  }
}

/* ==========================================================
   LOAD WEEK OPTIONS
========================================================== */
function loadWeekOptions() {
  if (!weekInput) {
    console.error("❌ pbp-week-input element missing");
    return;
  }

  weekInput.innerHTML = "";

  const allOpt = document.createElement("option");
  allOpt.value = "ALL";
  allOpt.textContent = "ALL Weeks";
  weekInput.appendChild(allOpt);

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
   NORMALIZATION (SAFE)
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

function normalizePBP(raw) {
  return {
    ...raw,
    game_id: text(raw.game_id),
    play_id: text(raw.play_id),
    posteam: text(raw.posteam),
    defteam: text(raw.defteam),
    desc: text(raw.desc),
    yards_gained: num(raw.yards_gained),
    epa: num(raw.epa),
    success: raw.success ? "✓" : ""
  };
}

/* ==========================================================
   LOAD MULTI-WEEK PBP (FIXED)
========================================================== */
async function loadMultiPBP() {
  const season = Number(seasonInput?.value);
  const weeks = getSelectedWeeks();
  const weekParam = weeks.join(",");

  if (!pbpBody || !tableWrapper || !loadingIndicator) {
    console.error("❌ Missing required DOM elements for PBP rendering");
    return;
  }

  pbpBody.innerHTML = "";
  tableWrapper.classList.add("hidden");
  loadingIndicator.classList.remove("hidden");

  try {
    const res = await fetch(
      `${BACKEND_URL}/nfl/multi-pbp/${season}?weeks=${weekParam}`
    );

    if (!res.ok) throw new Error(`Backend returned ${res.status}`);

    const payload = await res.json();
    const rows = Array.isArray(payload) ? payload : [];

    pbpData = rows.map(normalizePBP);

    renderTable(pbpData);

    // OPTIONAL: show charts if present
    if (chartsContainer) {
      chartsContainer.classList.remove("hidden");
      // future: renderEPAChart(pbpData)
    }

  } catch (err) {
    console.error("❌ Error loading multi-week PBP:", err);
    pbpBody.innerHTML = `<tr><td colspan="10">Error loading data.</td></tr>`;
  } finally {
    loadingIndicator.classList.add("hidden");
    tableWrapper.classList.remove("hidden");
  }
}

/* ==========================================================
   TABLE RENDERING (SAFE)
========================================================== */
function renderTable(data) {
  if (!pbpBody) return;

  if (!data.length) {
    pbpBody.innerHTML = `<tr><td colspan="10">No PBP data returned.</td></tr>`;
    return;
  }

  pbpBody.innerHTML = data
    .map(p => `
      <tr>
        <td>${p.game_id}</td>
        <td>${p.play_id}</td>
        <td>${p.posteam}</td>
        <td>${p.defteam}</td>
        <td>${p.desc}</td>
        <td>${p.yards_gained}</td>
        <td>${p.epa.toFixed(3)}</td>
        <td>${p.success}</td>
      </tr>
    `)
    .join("");
}

/* ==========================================================
   INIT
========================================================== */
document.addEventListener("DOMContentLoaded", () => {
  loadSeasons();
  loadWeekOptions();
});

/* ==========================================================
   EVENT BINDINGS (SAFE)
========================================================== */
loadBtn?.addEventListener("click", loadMultiPBP);

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

