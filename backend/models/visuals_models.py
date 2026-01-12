from pydantic import BaseModel
from typing import List, Optional

class VisualData(BaseModel):
    labels: List[str]
    points: List[int]
    error: Optional[str] = None
