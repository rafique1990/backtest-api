from app.backtest.weighting.equal import EqualWeighting
from app.core.exceptions import InvalidBacktestConfiguration


def get_weighting(rules) -> EqualWeighting:
    """
    Factory function to get weighting instance.

    Args:
        rules: WeightingScheme object or dict-like with weighting_type

    Returns:
        EqualWeighting instance

    Raises:
        InvalidBacktestConfiguration: If weighting type is unknown
    """
    # Handle both Pydantic models and dict-like objects
    if hasattr(rules, "weighting_type"):
        weighting_type = rules.weighting_type
    elif isinstance(rules, dict) and "weighting_type" in rules:
        weighting_type = rules["weighting_type"]
    else:
        raise InvalidBacktestConfiguration(
            f"Invalid weighting scheme format: {type(rules)}"
        )

    if weighting_type == "Equal":
        return EqualWeighting(rules)

    raise InvalidBacktestConfiguration(
        f"Unknown weighting type: '{weighting_type}'. Available options: ['Equal']"
    )
