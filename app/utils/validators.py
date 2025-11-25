def validate_data_field(v: str) -> str:
    """
    Validate data_field against allowed values.

    Args:
        v: Field name to validate

    Returns:
        Validated field name

    Raises:
        ValueError: If field is not in allowed list
    """
    allowed_fields = ["market_capitalization", "prices", "volume", "adtv_3_month"]
    if v not in allowed_fields:
        raise ValueError(f"Invalid data_field: {v}. Must be one of {allowed_fields}")
    return v
