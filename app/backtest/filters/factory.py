from app.backtest.filters.topn import TopNFilter
from app.core.exceptions import InvalidBacktestConfiguration


def get_filter(rules) -> TopNFilter:
    """
    Factory function to get filter instance.

    Args:
        rules: PortfolioCreation object or dict-like with filter_type

    Returns:
        TopNFilter instance

    Raises:
        InvalidBacktestConfiguration: If filter type is unknown
    """
    # Handle both Pydantic models and dict-like objects
    if hasattr(rules, "filter_type"):
        filter_type = rules.filter_type
    elif isinstance(rules, dict) and "filter_type" in rules:
        filter_type = rules["filter_type"]
    else:
        raise InvalidBacktestConfiguration(
            f"Invalid portfolio creation rules format: {type(rules)}"
        )

    if filter_type == "TopN":
        return TopNFilter(rules)

    raise InvalidBacktestConfiguration(
        f"Unknown filter type: '{filter_type}'. Available options: ['TopN']"
    )
