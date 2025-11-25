from pydantic import field_validator
from typing import Any

def validate_data_field(v: str) -> str:
    allowed_fields = [
        "market_capitalization",
        "prices",
        "volume",
        "adtv_3_month"
    ]
    if v not in allowed_fields:
        raise ValueError(f"Invalid data_field: {v}. Must be one of {allowed_fields}")
    return v
