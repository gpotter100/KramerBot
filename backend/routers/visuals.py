# backend/routers/visuals.py

from fastapi import APIRouter
from services.visuals_engine import build_visuals

router = APIRouter(prefix="/visuals", tags=["Visuals"])


@router.get("/")
def visuals():
    """
    Returns chart-ready arrays (labels + points) only.
    No raw rows, no CSV export.
    """
    return build_visuals()
