import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests import test_snap_counts

print('running tests...')
test_snap_counts.test_snap_counts_has_snap_pct()
test_snap_counts.test_snap_counts_some_positive()
print('ALL TESTS PASSED')
