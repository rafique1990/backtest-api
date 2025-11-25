import pathlib

import numpy as np
import pandas as pd

from app.core.config import settings

script_path = pathlib.Path(__file__).resolve()
PROJECT_ROOT = script_path.parent.parent
base_path = PROJECT_ROOT / settings.LOCAL_DATA_DIR.strip(
    "./"
)  # Use "data" part of "./data"

# Define the data fields to generate
data_field_identifiers = ["market_capitalization", "prices", "volume", "adtv_3_month"]

# Define the dimensions of the generated data
securities = list(
    map(str, range(1000))
)  # 1000 unique security identifiers (SEC_0 to SEC_999)
dates = pd.date_range("2020-01-01", "2025-01-22")
base_path.mkdir(parents=True, exist_ok=True)

for data_field_identifier in data_field_identifiers:
    # Generate random data ,Dimensions: (Number of Dates, Number of Securities)
    data = np.random.uniform(low=1, high=100, size=(len(dates), len(securities)))

    data_df = pd.DataFrame(data, index=dates, columns=[f"SEC_{s}" for s in securities])

    file_path = base_path / f"{data_field_identifier}.parquet"
    data_df.to_parquet(file_path)

    print(f"Successfully created: {file_path}")
