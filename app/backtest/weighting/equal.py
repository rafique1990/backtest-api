from app.backtest.weighting.base import BaseWeighting


class EqualWeighting(BaseWeighting):
    def __init__(self, rules=None):
        """
        Initialize with weighting rules (not used for equal weighting).

        Args:
            rules: WeightingScheme object (optional)
        """
        # Equal weighting doesn't need any special rules
        pass

    def calculate(self, assets: list[str]) -> dict[str, float]:
        """
        Calculate equal weights for all assets.

        Args:
            assets: List of asset identifiers

        Returns:
            Dictionary mapping asset to weight
        """
        if not assets:
            return {}

        weight = 1.0 / len(assets)
        return {asset: round(weight, 6) for asset in assets}
