# backend/services/visuals_engine.py

from typing import Dict, Any, List
from utils.data_store import get_data
from models.visuals_models import VisualData


def build_visuals() -> Dict[str, Any]:
    data = get_data()

    if not data:
        return {"error": "No data uploaded"}

    labels: List[str] = []
    points: List[int] = []

    for row in data:
        team = row.get("team")
        raw_points = row.get("points")
        if not team or raw_points in (None, ""):
            continue
        try:
            labels.append(str(team))
            points.append(int(raw_points))
        except ValueError:
            continue

    if not labels or not points:
        return {"error": "No valid team/points data for visuals"}

    visual = VisualData(labels=labels, points=points)
    return visual.model_dump()
