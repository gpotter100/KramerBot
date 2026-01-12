from pydantic import BaseModel
from typing import Optional

class BasicStats(BaseModel):
    team_count: int
    avg_points: float
    max_points: int
    min_points: int
    error: Optional[str] = None
