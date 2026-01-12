# backend/services/csv_parser.py

import csv
from io import StringIO
from typing import List, Dict, Any
from fastapi import UploadFile


async def parse_csv(file: UploadFile) -> List[Dict[str, Any]]:
    """
    Parse an uploaded CSV into a list of dict rows.
    """
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(StringIO(decoded))
    return list(reader)
