import sys, pathlib, os
# ensure backend/ is importable
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
# change cwd to backend so main mounts resolve
os.chdir(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
import main as backend_main

client = TestClient(backend_main.app)

seasons = list(range(2019, 2025))
weeks = list(range(1, 18))

results = []

total_players = 0
total_zero_fp = 0
total_zero_ppr = 0

for season in seasons:
    for week in weeks:
        try:
            resp = client.get(f"/nfl/player-usage/{season}/{week}")
        except Exception as e:
            print(f"{season} W{week}: request failed: {e}")
            continue
        if resp.status_code != 200:
            print(f"{season} W{week}: status {resp.status_code}")
            continue
        data = resp.json()
        if not data:
            # no data available for this week
            continue
        n = len(data)
        z_fp = sum(1 for r in data if (r.get('fantasy_points') is None or r.get('fantasy_points') == 0))
        z_ppr = sum(1 for r in data if (r.get('fantasy_points_ppr') is None or r.get('fantasy_points_ppr') == 0))
        pct_fp = 100.0 * z_fp / n
        pct_ppr = 100.0 * z_ppr / n
        results.append((season, week, n, z_fp, pct_fp, z_ppr, pct_ppr))
        total_players += n
        total_zero_fp += z_fp
        total_zero_ppr += z_ppr

# summarize
if not results:
    print('No data collected')
    raise SystemExit(0)

results.sort(key=lambda t: t[4], reverse=True)  # sort by pct_fp desc

print('\nTop 10 weeks by percent ZERO fantasy_points:')
for row in results[:10]:
    s,w,n,z,pct, z_ppr, pct_ppr = row
    print(f"{s}-W{w}: {pct:.1f}% zero ({z}/{n}) | ppr {pct_ppr:.1f}%")

avg_pct_fp = 100.0 * total_zero_fp / total_players
avg_pct_ppr = 100.0 * total_zero_ppr / total_players
print(f"\nOverall across {len(results)} weeks: players={total_players}, avg_zero_fp={avg_pct_fp:.1f}%, avg_zero_ppr={avg_pct_ppr:.1f}%")

# also show seasonal averages
season_map = {}
for s,w,n,z,pct, z_ppr, pct_ppr in results:
    season_map.setdefault(s, []).append((n,z,z_ppr))

print('\nSeasonal averages:')
for s in sorted(season_map.keys()):
    rows = season_map[s]
    tot = sum(r[0] for r in rows)
    ztot = sum(r[1] for r in rows)
    ztot_ppr = sum(r[2] for r in rows)
    print(f"{s}: avg_zero_fp={100.0*ztot/tot:.1f}% | avg_zero_ppr={100.0*ztot_ppr/tot:.1f}%")

print('\nAudit complete.')
