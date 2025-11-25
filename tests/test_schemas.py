import logging
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import (
    BacktestRequest,
    CalendarRules,
    PortfolioCreation,
    WeightingScheme,
)

logger = logging.getLogger(__name__)


def test_calendar_rules_valid():
    """Test valid CalendarRules with Quarterly type and dates"""
    rule = CalendarRules(rule_type="Quarterly", initial_date="2024-01-01")
    assert rule.rule_type == "Quarterly"
    assert rule.initial_date == date(2024, 1, 1)


def test_calendar_rules_invalid_date():
    """Test CalendarRules with invalid date format"""
    with pytest.raises(ValidationError):
        CalendarRules(rule_type="Quarterly", initial_date="invalid-date")


def test_portfolio_creation_valid():
    """Test valid PortfolioCreation"""
    filter_obj = PortfolioCreation(
        filter_type="TopN", n=50, data_field="market_capitalization"
    )
    assert filter_obj.filter_type == "TopN"
    assert filter_obj.n == 50


def test_backtest_request_valid():
    """Test valid BacktestRequest construction"""
    req = BacktestRequest(
        calendar_rules=CalendarRules(rule_type="Quarterly", initial_date="2024-01-01"),
        portfolio_creation=PortfolioCreation(
            filter_type="TopN", n=10, data_field="volume"
        ),
        weighting_scheme=WeightingScheme(weighting_type="Equal"),
    )
    assert isinstance(req.calendar_rules, CalendarRules)
    assert req.portfolio_creation.n == 10
