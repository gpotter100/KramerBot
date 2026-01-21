"""Inspect nflverse player_stats parquet for snap-related columns.

Usage:
  python backend/scripts/inspect_snap_parquet.py --season 2024
"""
import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--season", type=int, default=2024)
parser.add_argument("--show-sample", type=int, default=10, help="How many sample rows to print for non-zero snaps")
args = parser.parse_args()

season = args.season
url = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    f"player_stats/player_stats_{season}.parquet"
)

print(f"Loading player_stats parquet for season={season}\nURL: {url}\n")

try:
    df = pd.read_parquet(url)
except Exception as e:
    print("Failed to read parquet:", e)
    raise

print("Columns:", list(df.columns))

# normalize lowercase
df.columns = [c.lower() for c in df.columns]

# optional week filter info
has_week = "week" in df.columns
if has_week:
    print("Parquet contains 'week' column; weeks present:", sorted(df['week'].unique())[:10])

total = len(df)
print(f"Total rows in player_stats: {total}\n")

candidates = [
    'offense_snaps', 'offense_total', 'offense_pct', 'offense_snap_pct',
    'offense_pct_', 'offense_snap_pct_', 'offense_pct__', 'offense_snap_pct__'
]

found = [c for c in candidates if c in df.columns]
print("Found snap-related columns:", found)

# Report counts for common columns
def count_positive(col):
    if col in df.columns:
        nonzero = df[col].fillna(0) > 0
        return int(nonzero.sum())
    return 0

counts = {
    'offense_snaps>0': count_positive('offense_snaps'),
    'offense_total>0': count_positive('offense_total'),
    'offense_snap_pct>0': count_positive('offense_snap_pct'),
    'offense_pct>0': count_positive('offense_pct'),
    'snap_pct>0 (alias)': count_positive('snap_pct'),
}

print("Counts of positive snap fields:")
for k, v in counts.items():
    print(f"  {k}: {v}")

# If raw columns present, compute derived snap_pct and count
if 'offense_snaps' in df.columns and 'offense_total' in df.columns:
    df['_computed_snap_pct'] = df.apply(
        lambda r: (r['offense_snaps']/r['offense_total']) if r['offense_total'] not in [0, None] else 0,
        axis=1
    )
    print("Computed snap_pct > 0 count:", int((df['_computed_snap_pct'] > 0).sum()))

# Print sample rows where any snap indicator is non-zero
mask = pd.Series(False, index=df.index)
for col in ['offense_snaps', 'offense_total', 'offense_snap_pct', 'offense_pct', 'snap_pct', '_computed_snap_pct']:
    if col in df.columns:
        mask = mask | (df[col].fillna(0) > 0)

print('\nRows with any snap indicator > 0:', int(mask.sum()))
if mask.any():
    print(df.loc[mask, ['player_id','player_name','team','week'] + [c for c in ['offense_snaps','offense_total','offense_snap_pct','offense_pct','snap_pct','_computed_snap_pct'] if c in df.columns]].head(args.show_sample).to_string(index=False))
else:
    print('No non-zero snap rows found in the parquet sample.')

print('\nInspect complete.')
