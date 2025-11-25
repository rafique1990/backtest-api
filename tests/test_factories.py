import pytest

from app.backtest.calendar.factory import get_calendar
from app.backtest.filters.factory import get_filter
from app.backtest.weighting.factory import get_weighting
from app.core.exceptions import InvalidBacktestConfiguration
from app.schemas import CalendarRules, PortfolioCreation, WeightingScheme


class TestFactories:
    def test_calendar_factory_success(self):
        """Test calendar factory with valid rule type."""
        rules = CalendarRules(rule_type="Quarterly", initial_date="2024-01-01")
        calendar = get_calendar(rules)

        assert calendar is not None
        assert hasattr(calendar, "generate_dates")

    def test_calendar_factory_invalid_type(self):
        """Test calendar factory with invalid rule type."""

        # We need to test the factory directly with invalid data
        # since Pydantic won't let us create invalid models
        class InvalidCalendarRules:
            def __init__(self):
                self.rule_type = "InvalidType"
                self.initial_date = "2024-01-01"

        invalid_rules = InvalidCalendarRules()

        with pytest.raises(InvalidBacktestConfiguration, match="Unknown calendar type"):
            get_calendar(invalid_rules)

    def test_filter_factory_success(self):
        """Test filter factory with valid filter type."""
        rules = PortfolioCreation(
            filter_type="TopN", n=10, data_field="market_capitalization"
        )
        filter_obj = get_filter(rules)

        assert filter_obj is not None
        assert hasattr(filter_obj, "select")

    def test_filter_factory_invalid_type(self):
        """Test filter factory with invalid filter type."""

        class InvalidPortfolioCreation:
            def __init__(self):
                self.filter_type = "InvalidFilter"
                self.n = 10
                self.data_field = "market_capitalization"

        invalid_rules = InvalidPortfolioCreation()

        with pytest.raises(InvalidBacktestConfiguration, match="Unknown filter type"):
            get_filter(invalid_rules)

    def test_weighting_factory_success(self):
        """Test weighting factory with valid weighting type."""
        rules = WeightingScheme(weighting_type="Equal")
        weighting = get_weighting(rules)

        assert weighting is not None
        assert hasattr(weighting, "calculate")

    def test_weighting_factory_invalid_type(self):
        """Test weighting factory with invalid weighting type."""

        class InvalidWeightingScheme:
            def __init__(self):
                self.weighting_type = "InvalidWeighting"

        invalid_rules = InvalidWeightingScheme()

        with pytest.raises(
            InvalidBacktestConfiguration, match="Unknown weighting type"
        ):
            get_weighting(invalid_rules)

    def test_calendar_factory_with_dict_input(self):
        """Test calendar factory with dictionary input (edge case)."""
        rules_dict = {"rule_type": "Quarterly", "initial_date": "2024-01-01"}

        rules = CalendarRules(**rules_dict)
        calendar = get_calendar(rules)
        assert calendar is not None

    def test_filter_factory_edge_cases(self):
        """Test filter factory with edge cases."""
        # Test with different n values
        rules_small = PortfolioCreation(
            filter_type="TopN", n=1, data_field="market_capitalization"
        )
        rules_large = PortfolioCreation(filter_type="TopN", n=1000, data_field="volume")

        filter_small = get_filter(rules_small)
        filter_large = get_filter(rules_large)

        assert filter_small is not None
        assert filter_large is not None

    def test_weighting_factory_edge_cases(self):
        """Test weighting factory with edge cases."""
        # Test multiple valid instances
        rules1 = WeightingScheme(weighting_type="Equal")
        rules2 = WeightingScheme(weighting_type="Equal")

        weighting1 = get_weighting(rules1)
        weighting2 = get_weighting(rules2)

        # Should return different instances
        assert weighting1 is not None
        assert weighting2 is not None
        assert weighting1 != weighting2
