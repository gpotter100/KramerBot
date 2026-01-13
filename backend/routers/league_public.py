# backend/routers/league_public.py

from fastapi import APIRouter, HTTPException
from services.cbs_public import get_standings, LeagueDataError

router = APIRouter(prefix="/league/public", tags=["LeaguePublic"])

@router.get("/standings")
async def league_standings():
  try:
      data = await get_standings()
      return {"standings": data}
  except LeagueDataError as e:
      raise HTTPException(status_code=502, detail=str(e))
  except Exception:
      raise HTTPException(status_code=500, detail="Unexpected error fetching league standings")
