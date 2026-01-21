import sys, pathlib, os
# ensure backend/ is importable
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
# change cwd to backend so main mounts resolve
os.chdir(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
import main as backend_main

client = TestClient(backend_main.app)

checks = [
    (2024, 1),
    (2024, 2),
    (2023, 1),
    (2021, 17),
    (2019, 1),
]

fields = ["player_name", "team", "position", "fantasy_points", "fantasy_points_ppr", "fantasy_points_half", "fantasy_points_0.5ppr"]

for season, week in checks:
    print(f"\n== Season {season} Week {week} ==")
    resp = client.get(f"/nfl/player-usage/{season}/{week}")
    print("status_code:", resp.status_code)
    try:
        data = resp.json()
    except Exception as e:
        print("failed to parse json:", e)
        print(resp.text)
        continue

    if not data:
        print("no data returned")
        continue

    # sort locally by fantasy_points desc
    sorted_rows = sorted(data, key=lambda r: r.get("fantasy_points", 0), reverse=True)
    top5 = sorted_rows[:5]
    for i, row in enumerate(top5, 1):
        out = {k: row.get(k) for k in fields if k in row}
        print(f"#{i}", out)

print("\nSpot-check completed.")
