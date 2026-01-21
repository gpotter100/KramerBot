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

summary = {
    'total_players': 0,
    'total_zero_fp': 0,
    'total_zero_ppr': 0,
    'snap_players': 0,
    'snap_zero_fp': 0,
    'snap_zero_ppr': 0,
    'touch_players': 0,
    'touch_zero_fp': 0,
    'touch_zero_ppr': 0,
}

errors = []

for season in seasons:
    for week in weeks:
        try:
            resp = client.get(f"/nfl/player-usage/{season}/{week}")
        except Exception as e:
            errors.append((season, week, str(e)))
            continue
        if resp.status_code != 200:
            errors.append((season, week, f"status {resp.status_code}"))
            continue
        data = resp.json()
        if not data:
            continue

        for r in data:
            summary['total_players'] += 1
            if (r.get('fantasy_points') is None) or (r.get('fantasy_points') == 0):
                summary['total_zero_fp'] += 1
            if (r.get('fantasy_points_ppr') is None) or (r.get('fantasy_points_ppr') == 0):
                summary['total_zero_ppr'] += 1

            snap_pct = r.get('snap_pct') or r.get('snap_pct_', 0) or 0
            touches = r.get('touches', 0)

            if snap_pct and snap_pct > 0:
                summary['snap_players'] += 1
                if (r.get('fantasy_points') is None) or (r.get('fantasy_points') == 0):
                    summary['snap_zero_fp'] += 1
                if (r.get('fantasy_points_ppr') is None) or (r.get('fantasy_points_ppr') == 0):
                    summary['snap_zero_ppr'] += 1

            if touches and touches > 0:
                summary['touch_players'] += 1
                if (r.get('fantasy_points') is None) or (r.get('fantasy_points') == 0):
                    summary['touch_zero_fp'] += 1
                if (r.get('fantasy_points_ppr') is None) or (r.get('fantasy_points_ppr') == 0):
                    summary['touch_zero_ppr'] += 1

# Print results
print('\nFiltered Audit Results (2019-2024, weeks 1-17):')
print(f"Total player rows examined: {summary['total_players']}")
print(f"Overall zero fantasy_points: {summary['total_zero_fp']} ({100.0*summary['total_zero_fp']/summary['total_players']:.1f}%)")
print(f"Overall zero fantasy_points_ppr: {summary['total_zero_ppr']} ({100.0*summary['total_zero_ppr']/summary['total_players']:.1f}%)")

if summary['snap_players'] > 0:
    print('\nPlayers with snap_pct>0:')
    print(f" Count: {summary['snap_players']}")
    print(f" Zero fantasy_points among snap players: {summary['snap_zero_fp']} ({100.0*summary['snap_zero_fp']/summary['snap_players']:.1f}%)")
    print(f" Zero fantasy_points_ppr among snap players: {summary['snap_zero_ppr']} ({100.0*summary['snap_zero_ppr']/summary['snap_players']:.1f}%)")
else:
    print('\nNo snap_pct>0 players found in the sample.')

if summary['touch_players'] > 0:
    print('\nPlayers with touches>0:')
    print(f" Count: {summary['touch_players']}")
    print(f" Zero fantasy_points among touch players: {summary['touch_zero_fp']} ({100.0*summary['touch_zero_fp']/summary['touch_players']:.1f}%)")
    print(f" Zero fantasy_points_ppr among touch players: {summary['touch_zero_ppr']} ({100.0*summary['touch_zero_ppr']/summary['touch_players']:.1f}%)")
else:
    print('\nNo touches>0 players found in the sample.')

if errors:
    print('\nSome weeks failed to load:')
    for e in errors[:10]:
        print(' ', e)
    if len(errors) > 10:
        print(' ...', len(errors)-10, 'more')

print('\nFiltered audit complete.')
