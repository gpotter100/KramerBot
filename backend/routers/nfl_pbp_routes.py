from fastapi import APIRouter, HTTPException, Query

from services.nfl_pbp_service import (
    pbp_games_index,
    pbp_by_game,
)

router = APIRouter(prefix="/nfl", tags=["nfl"])


@router.get("/pbp/health")
def pbp_health():
    """
    Lightweight health check to confirm the PBP router is mounted
    and the service is reachable.
    """
    return {"status": "ok"}


@router.get("/pbp/{season}/{week}/games")
def get_pbp_games(
    season: int,
    week: int,
    season_type: str = Query("REG", pattern="^(REG|POST)$"),
):
    """
    Returns a small, stable index of games for a given week.
    Intended for dropdowns and selectors — never hard-fails.
    """
    try:
        games = pbp_games_index(season, week, season_type)
        return games if isinstance(games, list) else []
    except Exception:
        # Never break the UI for a dropdown
        return []


@router.get("/pbp/{season}/{week}")
def get_pbp(
    season: int,
    week: int,
    game_id: str = Query(..., min_length=1),
    season_type: str = Query("REG", pattern="^(REG|POST)$"),
    limit: int | None = Query(
        None,
        ge=1,
        le=1000,
        description="Optional max number of plays to return",
    ),
):
    """
    Returns play-by-play for a single game.
    Payload is intentionally trimmed for browser safety.
    """
    try:
        return pbp_by_game(
            season=season,
            week=week,
            game_id=game_id,
            season_type=season_type,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load play-by-play: {e}",
        )
