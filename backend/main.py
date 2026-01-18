# backend/main.py
print(">>> RUNNING MAIN FROM:", __file__)

import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------

from routers.chat import chat_router
from routers.upload import router as upload_router
from routers.stats import router as stats_router
from routers.visuals import router as visuals_router
from routers.league_public import router as league_public_router
from routers.nfl_pbp_routes import router as nfl_pbp_router

# IMPORTANT: use the router-based NFL system
from routers import nfl_router

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
# INCLUDE ROUTERS
# ---------------------------------------------------------

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(stats_router)
app.include_router(visuals_router)
app.include_router(league_public_router)
app.include_router(nfl_pbp_router)

# The correct NFL router (Option A)
app.include_router(nfl_router)

app.mount("/styles", StaticFiles(directory="../frontend/styles"), name="styles")

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
