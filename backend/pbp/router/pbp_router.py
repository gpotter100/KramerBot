from fastapi import APIRouter
from pbp.loaders.orchestrator import load_pbp_for_season
from pbp.metrics.epa import add_success
from pbp.aggregate.players import aggregate_qb_efficiency

router = APIRouter()

@router.get("/nfl/pbp/qb-efficiency/{season}")
def get_qb_efficiency(season: int):
    lf = load_pbp_for_season(season)
    lf = add_success(lf)
    df = aggregate_qb_efficiency(lf)
    return df.to_dicts()
