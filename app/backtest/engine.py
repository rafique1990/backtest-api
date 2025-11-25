import logging
import time
from datetime import date
from typing import Dict, List, Tuple

from app.schemas import (
    BacktestRequest,
    PerformanceMetrics,
    StrategySummary,
    BacktestWeights,
)
from app.services.base_data_service import BaseDataService
from app.backtest.calendar.factory import get_calendar
from app.backtest.portfolio_selector import PortfolioSelector
from app.core.exceptions import CalendarRuleError

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Orchestrates portfolio backtesting with configurable strategies."""

    def __init__(self, data_service: BaseDataService):
        self.data_service = data_service

    def run(
        self, request: BacktestRequest
    ) -> Tuple[Dict[str, Dict[str, float]], PerformanceMetrics, List[str]]:
        """
        Execute backtest strategy over rebalance dates.
        
        Args:
            request: Backtest configuration with calendar, filter, and weighting rules
            
        Returns:
            Tuple of (weights_dict, performance_metrics, warnings)
        """
        start_time = time.time()
        weights_series = []
        warnings = []

        try:
            available_range = self.data_service.get_data_range(
                request.portfolio_creation.data_field
            )
            self._validate_date_range(
                request.calendar_rules.initial_date, available_range
            )

            calendar = get_calendar(request.calendar_rules)
            rebalance_dates = calendar.generate_dates(
                request.calendar_rules.initial_date,
                date(2025, 1, 22),
            )

            portfolio_selector = PortfolioSelector(
                request.portfolio_creation, request.weighting_scheme
            )

            for rebalance_date in rebalance_dates:
                try:
                    daily_data = self.data_service.get_data_for_dates(
                        request.portfolio_creation.data_field,
                        [rebalance_date.isoformat()],
                    )

                    if daily_data.empty:
                        warnings.append(f"No data available for {rebalance_date}")
                        continue

                    asset_weights = portfolio_selector.select_and_weight(
                        daily_data, rebalance_date.isoformat()
                    )

                    if asset_weights:
                        weights_series.append(
                            BacktestWeights(
                                date=rebalance_date.isoformat(),
                                weights=asset_weights,
                                assets=list(asset_weights.keys()),
                            )
                        )
                    else:
                        warnings.append(f"No weights calculated for {rebalance_date}")

                except Exception as e:
                    warnings.append(f"Error processing {rebalance_date}: {str(e)}")
                    continue

            weights_dict = {weight.date: weight.weights for weight in weights_series}

            execution_time = time.time() - start_time
            strategy_summary = StrategySummary(
                calendar=request.calendar_rules.rule_type,
                filter=request.portfolio_creation.filter_type,
                weighting=request.weighting_scheme.weighting_type,
            )

            performance_metrics = PerformanceMetrics.create(
                execution_time=execution_time,
                weights=weights_dict,
                total_dates=len(rebalance_dates),
                strategy=strategy_summary,
            )

            return weights_dict, performance_metrics, warnings

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise

    def _validate_date_range(
        self, start_date: date, available_range: Tuple[date, date]
    ):
        """Validate that start date is within available data range."""
        min_avail, max_avail = available_range
        if start_date < min_avail or start_date > max_avail:
            raise CalendarRuleError(
                f"Start date {start_date} outside available range {min_avail} to {max_avail}"
            )
