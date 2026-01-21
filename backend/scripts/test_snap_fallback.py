"""Test load_snap_counts fallback behavior (adds backend to sys.path).
"""
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.snap_counts.loader import load_snap_counts

for season in [2024]:
    print(f"Testing season={season}")
    df = load_snap_counts(season, 1)
    print("Columns:", list(df.columns))
    if 'snap_pct' in df.columns:
        print('snap_pct>0 count:', int((df['snap_pct']>0).sum()))
        print(df[['player_id','player_name','team','snap_pct']].head(20).to_string(index=False))
    else:
        print('snap_pct missing')
