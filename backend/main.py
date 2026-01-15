# backend/main.py
print(">>> RUNNING MAIN FROM:", __file__)

import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Existing routers
from routers.chat import chat_router
from routers.upload import router as upload_router
from routers.stats import router as stats_router
from routers.visuals import router as visuals_router
from routers.league_public import router as league_public_router

# NEW: nflverse analytics imports
from analytics.nfl_data import (
    get_weekly_usage,
    get_top_usage,
    get_player_week
)

# ---------------------------------------------------------
# APP INIT
# ---------------------------------------------------------

app = FastAPI(title="KramerBot API", version="0.1.0")

# Read allowed origins from environment (Render)
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
print("🚀 Allowed CORS origins:", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(stats_router)
app.include_router(visuals_router)
app.include_router(league_public_router)

# ---------------------------------------------------------
# EXISTING ENDPOINTS
# ---------------------------------------------------------

@app.get("/standings")
def get_standings_file():
    try:
        with open("standings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_updated": None, "standings": []}


@app.get("/")
def root():
    return {"message": "KramerBot API running. Probably."}

# ---------------------------------------------------------
# NEW: NFLVERSE ANALYTICS ENDPOINTS
# ---------------------------------------------------------

@app.get("/nfl/player-usage/{season}/{week}")
def nfl_player_usage(season: int, week: int):
    """
    Raw weekly usage feed from nflverse.
    Perfect for KramerBot visuals or JARVIS reasoning.
    """
    data = get_weekly_usage(season, week)
    return {
        "season": season,
        "week": week,
        "players": data
    }


@app.get("/nfl/top-usage/{season}/{week}")
def nfl_top_usage(
    season: int,
    week: int,
    position: str | None = None,
    limit: int = 25
):
    """
    Top usage players for a given week.
    Optional filters:
      - position=RB
      - position=WR
      - limit=10
    """
    data = get_top_usage(season, week, position, limit)
    return {
        "season": season,
        "week": week,
        "position": position,
        "limit": limit,
        "players": data
    }


@app.get("/nfl/player-week/{season}/{week}/{player_name}")
def nfl_player_week(season: int, week: int, player_name: str):
    """
    Get a single player's weekly usage.
    Useful for:
      - JARVIS answering “How did Bijan do last week?”
      - KramerBot spotlight cards
    """
    data = get_player_week(season, week, player_name)
    return {
        "season": season,
        "week": week,
        "player": player_name,
        "results": data
    }
