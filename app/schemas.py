from datetime import date
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import validate_data_field


class CalendarRules(BaseModel):
    rule_type: Literal["Quarterly"] = "Quarterly"
    initial_date: date = Field(..., description="Start date for backtest")


class PortfolioCreation(BaseModel):
    filter_type: Literal["TopN"] = "TopN"
    n: int = Field(10, description="Number of top assets to select", gt=0)
    data_field: str = Field("market_capitalization", description="Field for ranking")

    @field_validator("data_field")
    @classmethod
    def validate_field(cls, v: str) -> str:
        return validate_data_field(v)


class WeightingScheme(BaseModel):
    weighting_type: Literal["Equal"] = "Equal"


class BacktestRequest(BaseModel):
    calendar_rules: CalendarRules
    portfolio_creation: PortfolioCreation
    weighting_scheme: WeightingScheme


class StrategySummary(BaseModel):
    calendar: str
    filter: str
    weighting: str


class PerformanceMetrics(BaseModel):
    execution_time: float = Field(..., description="Total execution time in seconds")
    rebalance_dates_processed: int = Field(
        ..., description="Number of successful rebalance dates"
    )
    total_rebalance_dates: int = Field(
        ..., description="Total rebalance dates attempted"
    )
    average_assets_per_rebalance: float = Field(
        ..., description="Average assets per rebalance period"
    )
    strategy: StrategySummary = Field(..., description="Strategy configuration summary")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def create(
        cls,
        execution_time: float,
        weights: dict[str, dict[str, float]],
        total_dates: int,
        strategy: StrategySummary,
    ) -> "PerformanceMetrics":
        return cls(
            execution_time=execution_time,
            rebalance_dates_processed=len(weights),
            total_rebalance_dates=total_dates,
            average_assets_per_rebalance=float(
                np.mean([len(w) for w in weights.values()]) if weights else 0.0
            ),
            strategy=strategy,
        )


class BacktestWeights(BaseModel):
    date: str = Field(..., description="Rebalance date in ISO format")
    weights: dict[str, float] = Field(..., description="Asset weights for this date")
    assets: list[str] = Field(..., description="List of assets in portfolio")


class BacktestResult(BaseModel):
    weights: list[BacktestWeights] = Field(
        ..., description="Time-series of portfolio weights"
    )
    performance: PerformanceMetrics = Field(..., description="Performance metrics")
    warnings: list[str] = Field(
        default_factory=list, description="Any warnings during execution"
    )


class BacktestResponse(BaseModel):
    execution_time: float = Field(..., description="Total execution time")
    weights: dict[str, dict[str, float]] = Field(
        ..., description="Portfolio weights by date"
    )
    metadata: PerformanceMetrics = Field(..., description="Performance metadata")
    warnings: list[str] = Field(default_factory=list, description="Execution warnings")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "execution_time": 1.234,
                "weights": {
                    "2024-03-31": {"AAPL": 0.5, "MSFT": 0.5},
                    "2024-06-30": {"GOOG": 0.33, "AMZN": 0.33, "TSLA": 0.34},
                },
                "metadata": {
                    "execution_time": 1.234,
                    "rebalance_dates_processed": 2,
                    "total_rebalance_dates": 4,
                    "average_assets_per_rebalance": 2.5,
                    "strategy": {
                        "calendar": "Quarterly",
                        "filter": "TopN",
                        "weighting": "Equal",
                    },
                },
                "warnings": ["Some warning message"],
            }
        }
    )


class PromptIn(BaseModel):
    prompt: str = Field(..., description="Natural language prompt for backtest")
