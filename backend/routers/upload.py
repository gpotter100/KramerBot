# backend/routers/upload.py

from fastapi import APIRouter, UploadFile, File
from services.csv_parser import parse_csv
from services.data_store_upload import store_data

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/")
async def upload_csv(file: UploadFile = File(...)):
    """
    Accepts a CSV, parses it, and stores rows in memory.
    Does NOT return raw data.
    """
    rows = await parse_csv(file)
    store_data(rows)
    return {"status": "ok", "message": f"CSV uploaded. Loaded {len(rows)} rows."}
