# backend/services/stats_engine.py

from typing import Dict, Any, List
from utils.data_store import get_data
from models.stats_models import BasicStats


def compute_basic_stats() -> Dict[str, Any]:
    data = get_data()

    if not data:
        return {"error": "No data uploaded"}

    # Expecting columns like: team, points
    points: List[int] = []
    for row in data:
        raw = row.get("points")
        if raw is None or raw == "":
            continue
        try:
            points.append(int(raw))
        except ValueError:
            continue

    if not points:
        return {"error": "No valid points data found"}

    team_count = len(data)
    avg_points = sum(points) / len(points)
    max_points = max(points)
    min_points = min(points)

    stats = BasicStats(
        team_count=team_count,
        avg_points=avg_points,
        max_points=max_points,
        min_points=min_points,
    )

    return stats.model_dump()
