import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import logging

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_sample_data():
    """Generate optimized sample parquet data for testing"""
    # 1. Get the absolute path of the project root (one level up from 'scripts/')
    project_root = Path(__file__).resolve().parent.parent

    # 2. Resolve DATA_DIR relative to the project root, not the command line location
    if Path(settings.DATA_DIR).is_absolute():
        data_path = Path(settings.DATA_DIR)
    else:
        # Joins project_root with "./data", ensuring it lands in the right place
        data_path = project_root / settings.DATA_DIR

    logger.info(f"Target Data Directory: {data_path}")

    data_path.mkdir(parents=True, exist_ok=True)

    data_field_identifiers = ["market_capitalization", "volume", "adtv_3_month"]

    securities = list(map(str, range(1000)))
    dates = pd.date_range("2020-01-01", "2025-01-22")

    logger.info(
        f"Generating data for {len(securities)} securities and {len(dates)} dates..."
    )

    for data_field_identifier in data_field_identifiers:
        # Generate realistic financial data with proper distributions
        if data_field_identifier == "market_capitalization":
            # Log-normal distribution for market caps (in millions)
            data = np.random.lognormal(
                mean=12, sigma=1.5, size=(len(dates), len(securities))
            )

        elif data_field_identifier in ["volume", "adtv_3_month"]:
            # Volume data with some autocorrelation
            base_volume = np.random.lognormal(
                mean=8, sigma=1.0, size=(len(dates), len(securities))
            )

            # Add some time series characteristics
            trend = np.linspace(1, 1.5, len(dates)).reshape(-1, 1)
            noise = np.random.normal(0, 0.1, size=(len(dates), len(securities)))

            data = base_volume * trend + noise
            data = np.abs(data)  # Ensure positive values

        df = pd.DataFrame(data, index=dates, columns=securities)

        file_path = data_path / f"{data_field_identifier}.parquet"

        # Use optimal parquet settings
        df.to_parquet(
            file_path,
            engine="pyarrow",
            compression="snappy",  # Good balance of speed and compression
            index=True,
        )

        memory_mb = df.memory_usage(deep=True).sum() / 1024**2
        logger.info(
            f"Generated {data_field_identifier}.parquet - Shape: {df.shape}, Memory: {memory_mb:.2f}MB"
        )

    logger.info("Data generation completed successfully!")


if __name__ == "__main__":
    generate_sample_data()
