import pandas as pd

from app.backtest.filters.base import BaseFilter


class TopNFilter(BaseFilter):
    def __init__(self, rules):
        """
        Initialize with portfolio creation rules.

        Args:
            rules: PortfolioCreation object with n and data_field
        """
        self.n = rules.n
        self.data_field = rules.data_field

    def select(self, data: pd.DataFrame, n: int = None) -> list[str]:
        """
        Select top N assets based on the specified data field.

        Args:
            data: DataFrame with securities as columns and single row for current date
            n: Optional override for number of assets to select

        Returns:
            List of selected security identifiers
        """
        if data.empty:
            return []

        # Use provided n or fall back to initialized n
        top_n = n if n is not None else self.n

        # Get the first row (current date data) and ensure numeric values
        current_data = data.iloc[0]

        # Convert to numeric, coercing errors to NaN
        current_data = pd.to_numeric(current_data, errors="coerce")

        # Drop NaN values that resulted from conversion
        current_data = current_data.dropna()

        if current_data.empty:
            return []

        # Sort descending by numeric values
        sorted_assets = current_data.sort_values(ascending=False)

        # Return top N security identifiers
        return sorted_assets.head(top_n).index.tolist()
