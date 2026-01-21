import sys, pathlib
# ensure backend/ is on sys.path so `import main` works (backend is app root)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import os
from fastapi.testclient import TestClient

# change working dir into backend so relative mounts in main.py resolve
os.chdir(str(pathlib.Path(__file__).resolve().parents[1]))
import main as backend_main
app = backend_main.app

client = TestClient(app)

resp = client.get('/nfl/player-usage/2024/1')
print('status_code:', resp.status_code)
try:
    data = resp.json()
    print('num_records:', len(data))
    if data:
        print('first_record_keys:', list(data[0].keys()))
        # print subset of keys including fantasy fields
        keys = ['player_name','team','position','fantasy_points','fantasy_points_ppr','fantasy_points_half','fantasy_points_0.5ppr']
        print({k: data[0].get(k) for k in keys if k in data[0]})
except Exception as e:
    print('failed to parse json:', e)
    print(resp.text)
