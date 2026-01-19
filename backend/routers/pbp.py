from fastapi import APIRouter, HTTPException
from weekly.loader import load_weekly_pbp   # You already have this or similar
from weekly.normalizer import normalize_pbp_row  # Your existing normalizer

router = APIRouter()

@router.get("/nfl/multi-pbp/{season}")
def get_multi_week_pbp(season: int, weeks: str):
    """
    Aggregate PBP rows across multiple weeks.
    Example:
    /nfl/multi-pbp/2025?weeks=1,2,3
    """

    # Parse week list
    try:
        week_list = [int(w) for w in weeks.split(",") if w.strip()]
    except:
        raise HTTPException(status_code=400, detail="Invalid weeks parameter")

    if not week_list:
        raise HTTPException(status_code=400, detail="No weeks provided")

    all_rows = []

    # Load each week’s PBP
    for w in week_list:
        try:
            df = load_weekly_pbp(season, w)
            rows = df.to_dict(orient="records")
            for r in rows:
                all_rows.append(normalize_pbp_row(r))
        except Exception as e:
            print(f"Error loading PBP for week {w}: {e}")

    return all_rows
