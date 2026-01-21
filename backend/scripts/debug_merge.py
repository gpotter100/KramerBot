"""Debug script: inspect weekly merge keys and sample merged rows.

Usage: run from project root with backend/venv Python.
"""
import pprint
import sys
from pathlib import Path

# Ensure backend package is importable when running script from repo root
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.loaders.pbp_weekly_loader import load_weekly_from_pbp
from services.loaders.id_harmonizer import harmonize_ids
from services.snap_counts.loader import load_snap_counts

SEASON = 2024
WEEK = 1

pp = pprint.PrettyPrinter(width=160)

print(f"Running debug_merge for season={SEASON} week={WEEK}\n")

# 1) Load weekly PBP-derived stats
weekly = load_weekly_from_pbp(SEASON, WEEK)
print("--- weekly columns ---")
print(list(weekly.columns))
print("--- weekly sample rows (first 10) ---")
pp.pprint(weekly.head(10).to_dict(orient="records"))

# Show player_id formats in weekly
print("--- weekly player_id samples ---")
print(weekly["player_id"].head(20).tolist())

# 2) Load roster via the router helper if available
try:
    from routers.nfl_router import load_rosters
    rosters = load_rosters(SEASON)
    print("--- roster columns ---")
    print(list(rosters.columns))
    print("--- roster sample rows (first 10) ---")
    pp.pprint(rosters.head(10).to_dict(orient="records"))
    print("--- roster player_id samples ---")
    print(rosters["player_id"].head(20).tolist())
except Exception as e:
    print("Could not load rosters via routers.nfl_router.load_rosters():", e)
    rosters = None

# 3) Harmonize IDs
if rosters is not None:
    merged = harmonize_ids(weekly, rosters)
    print("--- merged after harmonize_ids columns ---")
    print(list(merged.columns))
    print("--- merged sample rows (first 10) ---")
    pp.pprint(merged.head(10).to_dict(orient="records"))
    print("--- merged player_id samples ---")
    print(merged["player_id"].head(20).tolist())
else:
    merged = weekly

# 4) Load snap counts
snaps = load_snap_counts(SEASON, WEEK)
print("--- snaps columns ---")
print(list(snaps.columns))
print("--- snaps sample rows (first 10) ---")
pp.pprint(snaps.head(10).to_dict(orient="records"))
print("--- snaps player_id samples ---")
print(snaps["player_id"].head(20).tolist())

# 5) Merge snaps into merged DF (same logic as router)
if "player_id" in merged.columns and not snaps.empty:
    snaps_cols = [c.lower() for c in snaps.columns]
    snaps.columns = snaps_cols
    if "offense_pct" in snaps.columns:
        snaps = snaps.rename(columns={"offense_pct": "snap_pct"})
    else:
        snaps["snap_pct"] = snaps.get("snap_pct", 0)

    final = merged.merge(snaps[["player_id", "snap_pct"]], on="player_id", how="left")
    final["snap_pct"] = final["snap_pct"].fillna(0)
else:
    final = merged.copy()
    final["snap_pct"] = 0

print("--- final columns ---")
print(list(final.columns))
print("--- final sample rows (first 20) ---")
pp.pprint(final.head(20).to_dict(orient="records"))

# 6) Show any players with snap_pct>0
has_snaps = final[final["snap_pct"] > 0]
print(f"Players with snap_pct>0: {len(has_snaps)}")
if not has_snaps.empty:
    pp.pprint(has_snaps.head(20).to_dict(orient="records"))

print("\nDebug complete.")
