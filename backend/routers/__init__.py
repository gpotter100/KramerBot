# backend/routers/__init__.py

from .chat import chat_router
from .upload import router as upload_router
from .stats import router as stats_router
from .visuals import router as visuals_router
from .nfl_router import router as nfl_router
from .league_public import router as league_public_router
from .nfl_pbp_routes import router as nfl_pbp_router
from .pbp import router as pbp_router
from .attribution import router as attribution_router
from .player_usage import router as player_usage_router
