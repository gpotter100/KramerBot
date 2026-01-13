# backend/services/visuals_engine.py

from typing import Dict, Any, List
from utils.data_store import get_data
from models.visuals_models import VisualData


def build_visuals() -> Dict[str, Any]:
    """
    Converts stored CSV rows into chart-ready arrays.
    Always returns a dict with either:
      - { "labels": [...], "points": [...] }
      - { "error": "message" }
    Never raises exceptions.
    """

    data = get_data()

    # No CSV uploaded yet
    if not data:
        return {"error": "No data uploaded"}

    labels: List[str] = []
    points: List[int] = []

    for row in data:
        if not isinstance(row, dict):
            continue  # skip malformed rows

        team = row.get("team")
        raw_points = row.get("points")

        # Skip rows missing required fields
        if not team or raw_points in (None, ""):
            continue

        try:
            labels.append(str(team))
            points.append(int(raw_points))
        except (ValueError, TypeError):
            # Skip rows with non-numeric points
            continue

    # No usable data found
    if not labels or not points:
        return {"error": "No valid team/points data for visuals"}

    # Build typed response
    visual = VisualData(labels=labels, points=points)
    return visual.model_dump()
