# Copilot / AI Agent Instructions

This project is a small FastAPI + static frontend application focused on NFL PBP processing and analytics. The goal of these instructions is to help an AI coding agent get productive quickly and make safe, consistent changes.

- **Entrypoint**: backend/main.py is the FastAPI app. Routers live under backend/routers and services under backend/services. Mounts and CORS are configured in `backend/main.py`.

- **Key directories**:
  - backend/routers: API endpoints (each module typically exposes `router` or named router objects).
  - backend/services: business logic (loaders, presenters, fantasy scoring, metrics).
  - backend/data/pbp: local parquet PBP files named `pbp_<YEAR>.parquet` used by the NFL routes.
  - frontend/: static UI assets; backend mounts `../frontend/styles` as `/styles`.

- **Important files to reference**:
  - [backend/main.py](../backend/main.py) — app init and router registration
  - [backend/routers/nfl_router.py](../backend/routers/nfl_router.py) — NFL player-usage route patterns and season cache
  - [backend/services/presenters/usage_presenter.py](../backend/services/presenters/usage_presenter.py) — canonical grouping/aggregation logic
  - [backend/services/loaders/*] — ID harmonization and PBP loaders used across routes
  - backend/requirements.txt — Python dependencies to install

- **Common patterns / gotchas**:
  - Routers are included in `backend/main.py`. When adding a new router, either import it in `main.py` and `app.include_router(my_router)`, or follow existing patterns (some routers are imported with explicit names).
  - Many service modules avoid circular imports by performing imports inside functions (see `load_weekly_data` in `nfl_router.py`). Preserve this pattern when refactoring.
  - Data identity is canonicalized by `player_id` (see `present_usage` and `harmonize_ids`). Use `player_id` as the grouping key.
  - Local PBP files are preferred for speed; look under `backend/data/pbp`. Add new PBP files as `pbp_<YEAR>.parquet` if needed.
  - There is a simple in-memory season cache with a `CACHE_LOCK`—be careful when changing caching semantics.
  - Roster loader falls back from `player_id` to `gsis_id` or `nfl_id` if needed (see `load_rosters`). Honor those fallback behaviours.

- **Running locally (dev)**:

  1. Create/activate a Python venv. There is an `activate_venv.cmd` helper for Windows.

  2. Install dependencies from `backend/requirements.txt`:

```bash
python -m pip install -r backend/requirements.txt
```

  3. Run the API (from repository root):

```bash
# recommended for development
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

  - Set `CORS_ALLOWED_ORIGINS` environment variable if you need non-localhost frontend.
  - Static styles are served from `/styles` (mounted from `frontend/styles`).

- **Testing / verification**:
  - There are no formal test files in the repo root. Manual verification is via running the server and visiting endpoints, e.g. `/nfl/player-usage/2024/1` or `/nfl/seasons`.

- **Contributions guidelines for AI edits**:
  - Keep changes minimal and focused; follow existing module boundaries (routers vs services).
  - Preserve import-in-function patterns used to avoid circular imports.
  - When adding endpoints, prefer placing logic in `backend/services` and keep routers thin.
  - Avoid changing caching or data file locations without explicit reasoning; call out required migrations.

- **Search hints for common code**:
  - ID harmonization: search for `harmonize_ids` in `backend/services/loaders`
  - Presenting usage: `present_usage` in `backend/services/presenters`
  - Fantasy scoring: `apply_scoring` in `backend/services/fantasy`
  - Snap counts: `load_snap_counts` under `backend/services/snap_counts`

If anything above is unclear or you want additional examples (e.g., a sample router addition or a unit-test scaffold), tell me which area to expand and I will update this file.