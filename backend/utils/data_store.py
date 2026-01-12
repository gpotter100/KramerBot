# backend/utils/data_store.py

from typing import List, Dict, Any

_DATA: List[Dict[str, Any]] = []


def store_data(rows: List[Dict[str, Any]]) -> None:
    """
    Store parsed CSV rows in memory.
    Each row is a dict from csv.DictReader.
    """
    global _DATA
    _DATA = rows


def get_data() -> List[Dict[str, Any]]:
    """
    Internal access only. Do NOT expose this directly in any router.
    """
    return _DATA
