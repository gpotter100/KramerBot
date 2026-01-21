import pandas as pd
from backend.services.fantasy import scoring_engine as se

df = pd.DataFrame([{
    "passing_yards": 200,
    "passing_tds": 1,
    "interceptions": 0,
    "rushing_yards": 30,
    "rushing_tds": 0,
    "receiving_yards": 40,
    "receiving_tds": 0,
    "receptions": 5,
}])

# standard -> also shows PPR / half / 0.5ppr aliases
out = se.apply_standard_scoring(df)
print(out[["fantasy_points","fantasy_points_ppr","fantasy_points_half","fantasy_points_0.5ppr"]])