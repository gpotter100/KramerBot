import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.snap_counts.loader import load_snap_counts


def test_snap_counts_has_snap_pct():
    df = load_snap_counts(2024, 1)
    assert 'snap_pct' in df.columns


def test_snap_counts_some_positive():
    df = load_snap_counts(2024, 1)
    assert int((df['snap_pct'] > 0).sum()) > 0
