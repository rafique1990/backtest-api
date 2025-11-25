from datetime import date
from unittest.mock import Mock

import pandas as pd
import pytest

from app.backtest.engine import BacktestEngine
from app.core.exceptions import CalendarRuleError, DataNotFoundError
from app.schemas import (
    BacktestRequest,
    CalendarRules,
    PortfolioCreation,
    WeightingScheme,
)


class TestBacktestEngine:
    @pytest.fixture
    def mock_data_service(self):
        mock_service = Mock()
        mock_service.get_data_range.return_value = (date(2020, 1, 1), date(2025, 1, 22))
        return mock_service

    @pytest.fixture
    def backtest_engine(self, mock_data_service):
        return BacktestEngine(mock_data_service)

    @pytest.fixture
    def sample_request(self):
        return BacktestRequest(
            calendar_rules=CalendarRules(
                rule_type="Quarterly", initial_date=date(2024, 1, 1)
            ),
            portfolio_creation=PortfolioCreation(
                filter_type="TopN", n=5, data_field="market_capitalization"
            ),
            weighting_scheme=WeightingScheme(weighting_type="Equal"),
        )

    def test_run_successful_backtest(
        self, backtest_engine, mock_data_service, sample_request
    ):
        """Test successful backtest execution."""
        # Mock data for different dates
        mock_data = pd.DataFrame(
            {"AAPL": [100.0, 200.0], "MSFT": [150.0, 250.0], "GOOG": [120.0, 220.0]},
            index=pd.to_datetime(["2024-03-31", "2024-06-30"]),
        )

        mock_data_service.get_data_for_dates.return_value = mock_data

        weights, metrics, warnings = backtest_engine.run(sample_request)

        # Assertions
        assert isinstance(weights, dict)
        assert len(weights) > 0  # Should have some weights
        assert metrics.execution_time > 0
        assert metrics.rebalance_dates_processed > 0
        assert isinstance(warnings, list)

    def test_run_no_data_available(
        self, backtest_engine, mock_data_service, sample_request
    ):
        """Test backtest with no data available."""
        mock_data_service.get_data_for_dates.return_value = pd.DataFrame()  # Empty data

        weights, metrics, warnings = backtest_engine.run(sample_request)

        # Should have warnings but not crash
        assert len(warnings) > 0
        assert metrics.rebalance_dates_processed == 0

    def test_run_date_validation_failure(
        self, backtest_engine, mock_data_service, sample_request
    ):
        """Test backtest with date outside available range."""
        mock_data_service.get_data_range.return_value = (
            date(2024, 6, 1),
            date(2024, 6, 30),
        )

        with pytest.raises(CalendarRuleError):
            backtest_engine.run(sample_request)

    def test_run_data_service_error(
        self, backtest_engine, mock_data_service, sample_request
    ):
        """Test backtest when data service raises exception."""
        mock_data_service.get_data_range.side_effect = DataNotFoundError(
            "Data file not found"
        )

        with pytest.raises(DataNotFoundError):
            backtest_engine.run(sample_request)

    def test_validate_date_range_success(self, backtest_engine):
        """Test successful date range validation."""
        start_date = date(2023, 1, 1)
        available_range = (date(2020, 1, 1), date(2025, 1, 1))

        # Should not raise exception
        backtest_engine._validate_date_range(start_date, available_range)

    def test_validate_date_range_too_early(self, backtest_engine):
        """Test date range validation with start date too early."""
        start_date = date(2019, 1, 1)
        available_range = (date(2020, 1, 1), date(2025, 1, 1))

        with pytest.raises(CalendarRuleError):
            backtest_engine._validate_date_range(start_date, available_range)

    def test_validate_date_range_too_late(self, backtest_engine):
        """Test date range validation with start date too late."""
        start_date = date(2026, 1, 1)
        available_range = (date(2020, 1, 1), date(2025, 1, 1))

        with pytest.raises(CalendarRuleError):
            backtest_engine._validate_date_range(start_date, available_range)
