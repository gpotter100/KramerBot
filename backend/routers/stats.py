# backend/routers/stats.py

from fastapi import APIRouter
from services.stats_engine import compute_basic_stats

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/")
def stats():
    """
    Returns simple aggregate stats from the uploaded data.
    No raw rows, no CSV export.
    """
    return compute_basic_stats()
