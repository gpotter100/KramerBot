import { API_BASE as BACKEND_URL } from "./config.js";

const seasonInput = document.getElementById("season-input");
const weekInput = document.getElementById("week-input");

const pbpPanel = document.getElementById("pbp-panel");
const pbpGamesSelect = document.getElementById("pbp-games-select");
const pbpSeasonType = document.getElementById("pbp-season-type");
const pbpLoadBtn = document.getElementById("pbp-load-btn");
const pbpLoading = document.getElementById("pbp-loading");
const pbpBody = document.getElementById("pbp-body");

function setHidden(el, hidden) {
  if (!el) return;
  el.classList.toggle("hidden", hidden);
}

function text(v, fallback = "—") {
  if (v === undefined || v === null) return fallback;
  const s = String(v);
  return s.trim() === "" ? fallback : s;
}

async function loadGamesIndex() {
  const season = Number(seasonInput?.value);
  const week = Number(weekInput?.value);
  const seasonType = (pbpSeasonType?.value || "REG").toUpperCase();

  setHidden(pbpPanel, false);
  setHidden(pbpLoading, false);
  pbpGamesSelect.innerHTML = "";
  pbpBody.innerHTML = "";

  const url = `${BACKEND_URL}/nfl/pbp/${season}/${week}/games?season_type=${encodeURIComponent(seasonType)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`PBP games index failed: ${res.status}`);

  const games = await res.json();

  if (!Array.isArray(games) || games.length === 0) {
    pbpGamesSelect.innerHTML = `<option value="">No games found</option>`;
    return;
  }

  pbpGamesSelect.innerHTML = games
    .map(g => {
      const label = `${text(g.away_team)} @ ${text(g.home_team)}${g.game_date ? ` (${text(g.game_date).slice(0, 10)})` : ""}`;
      return `<option value="${text(g.game_id, "")}">${label}</option>`;
    })
    .join("");
}

async function loadPlays() {
  const season = Number(seasonInput?.value);
  const week = Number(weekInput?.value);
  const seasonType = (pbpSeasonType?.value || "REG").toUpperCase();
  const gameId = pbpGamesSelect?.value;

  if (!gameId) return;

  setHidden(pbpLoading, false);
  pbpBody.innerHTML = "";

  const url =
    `${BACKEND_URL}/nfl/pbp/${season}/${week}` +
    `?season_type=${encodeURIComponent(seasonType)}` +
    `&game_id=${encodeURIComponent(gameId)}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error(`PBP load failed: ${res.status}`);

  const plays = await res.json();
  const rows = Array.isArray(plays) ? plays : [];

  pbpBody.innerHTML = rows.map(p => `
    <tr>
      <td>${text(p.qtr)}</td>
      <td>${text(p.down)}</td>
      <td>${text(p.ydstogo)}</td>
      <td>${text(p.yardline_100)}</td>
      <td>${text(p.posteam)}</td>
      <td>${text(p.play_type)}</td>
      <td>${text(p.yards_gained)}</td>
      <td>${text(p.epa)}</td>
      <td>${text(p.wp)}</td>
      <td style="white-space: normal;">${text(p.desc)}</td>
    </tr>
  `).join("");
}

pbpLoadBtn?.addEventListener("click", async () => {
  try {
    await loadGamesIndex();
    await loadPlays();
  } catch (e) {
    console.error(e);
    pbpBody.innerHTML = `<tr><td colspan="10">Error loading play-by-play.</td></tr>`;
  } finally {
    setHidden(pbpLoading, true);
  }
});

pbpGamesSelect?.addEventListener("change", async () => {
  try {
    await loadPlays();
  } catch (e) {
    console.error(e);
  } finally {
    setHidden(pbpLoading, true);
  }
});
