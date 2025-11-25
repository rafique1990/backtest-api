import logging

import pandas as pd

from app.backtest.filters.factory import get_filter
from app.backtest.weighting.factory import get_weighting
from app.schemas import PortfolioCreation, WeightingScheme

logger = logging.getLogger(__name__)


class PortfolioSelector:
    def __init__(
        self, creation_config: PortfolioCreation, weighting_config: WeightingScheme
    ):
        self.portfolio_filter = get_filter(creation_config)
        self.weighting_strategy = get_weighting(weighting_config)
        self.n_securities = creation_config.n
        self.data_field = creation_config.data_field

    def select_and_weight(
        self, current_data: pd.DataFrame, date_str: str
    ) -> dict[str, float]:
        """
        Select assets and calculate weights for current date.

        Args:
            current_data: DataFrame with current date data
            date_str: Date string for logging

        Returns:
            Dictionary of asset weights
        """
        try:
            if current_data.empty:
                logger.warning(f"No data available for selection on {date_str}")
                return {}

            # Ensure data types are compatible for comparison
            # Convert any Timestamp objects to compatible types
            current_data = current_data.copy()

            # Convert index to string if it contains timestamps
            if hasattr(current_data.index, "strftime"):
                current_data.index = current_data.index.strftime("%Y-%m-%d")

            # Select assets using the filter
            selected_assets = self.portfolio_filter.select(
                current_data, self.n_securities
            )

            if len(selected_assets) < self.n_securities:
                logger.warning(
                    f"On {date_str}, only {len(selected_assets)} securities selected, "
                    f"requested {self.n_securities}"
                )

            # Calculate weights using the weighting strategy
            weights = self.weighting_strategy.calculate(selected_assets)

            logger.debug(
                f"Portfolio selection completed for {date_str}: {len(weights)} assets"
            )
            return weights

        except Exception as e:
            logger.error(f"Portfolio selection failed on {date_str}: {e}")
            return {}
