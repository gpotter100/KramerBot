# backend/routers/visuals.py

from fastapi import APIRouter
from services.visuals_engine import build_visuals

router = APIRouter(prefix="/visuals", tags=["Visuals"])

@router.get("/")
def visuals():
    print("📊 /visuals/ route hit")
    try:
        data = build_visuals()
        if not data:
            return {"error": "No visuals available yet."}
        return data
    except Exception as e:
        print("❌ Visuals engine error:", e)
        return {"error": "Visuals engine failed."}

