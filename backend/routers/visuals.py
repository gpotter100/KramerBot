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
    try:
        data = build_visuals()

        # If your engine returns None or empty, handle gracefully
        if not data:
            return {"error": "No visuals available yet."}

        return data

    except Exception as e:
        # Never expose internal errors to the frontend
        return {"error": "Visuals engine failed."}

