from app.backtest.calendar.quarterly import QuarterlyCalendar
from app.core.exceptions import InvalidBacktestConfiguration


def get_calendar(rules) -> QuarterlyCalendar:
    """
    Factory function to get calendar instance.

    Args:
        rules: CalendarRules object or dict-like with rule_type

    Returns:
        QuarterlyCalendar instance

    Raises:
        InvalidBacktestConfiguration: If calendar type is unknown
    """
    # Handle both Pydantic models and dict-like objects
    if hasattr(rules, "rule_type"):
        rule_type = rules.rule_type
    elif isinstance(rules, dict) and "rule_type" in rules:
        rule_type = rules["rule_type"]
    else:
        raise InvalidBacktestConfiguration(
            f"Invalid calendar rules format: {type(rules)}"
        )

    if rule_type == "Quarterly":
        return QuarterlyCalendar(rules)

    raise InvalidBacktestConfiguration(
        f"Unknown calendar type: '{rule_type}'. Available options: ['Quarterly']"
    )
