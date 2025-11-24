import pytest
import pandas as pd
from datetime import date
import os


@pytest.fixture(scope="session", autouse=True)
def ensure_test_data():
    """Ensure test data exists before running tests."""
    data_dir = "test_data"
    os.makedirs(data_dir, exist_ok=True)

    # Create minimal test data if needed
    test_fields = ["market_capitalization", "volume"]

    for field in test_fields:
        file_path = os.path.join(data_dir, f"{field}.parquet")
        if not os.path.exists(file_path):
            # Create simple test data
            dates = pd.date_range("2020-01-01", "2024-12-31", freq="D")
            securities = ["AAPL", "MSFT", "GOOG"]
            data = pd.DataFrame(
                [[100.0, 150.0, 200.0]] * len(dates), index=dates, columns=securities
            )
            data.to_parquet(file_path)

    yield

    # Cleanup
    import shutil

    shutil.rmtree(data_dir, ignore_errors=True)


@pytest.fixture
def sample_backtest_request():
    """Provide a sample backtest request for tests."""
    from app.schemas import (
        BacktestRequest,
        CalendarRules,
        PortfolioCreation,
        WeightingScheme,
    )

    return BacktestRequest(
        calendar_rules=CalendarRules(
            rule_type="Quarterly", initial_date=date(2024, 1, 1)
        ),
        portfolio_creation=PortfolioCreation(
            filter_type="TopN", n=5, data_field="market_capitalization"
        ),
        weighting_scheme=WeightingScheme(weighting_type="Equal"),
    )
