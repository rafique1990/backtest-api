from fastapi import APIRouter, HTTPException
import logging

from app.schemas import BacktestRequest, BacktestResponse, PromptIn
from app.api.dependencies import EngineDependency, NluServiceDependency


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/backtest", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest, engine: EngineDependency):
    try:
        weights, performance_metrics, warnings = engine.run(request)
        return BacktestResponse(
            execution_time=performance_metrics.execution_time,
            weights=weights,
            metadata=performance_metrics,
            warnings=warnings,
        )
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/backtest-prompt", response_model=BacktestResponse)
async def run_backtest_prompt(
    payload: PromptIn, engine: EngineDependency, nlu_service: NluServiceDependency
):
    try:
        request = await nlu_service.parse_prompt(payload.prompt)
        weights, performance_metrics, warnings = engine.run(request)
        return BacktestResponse(
            execution_time=performance_metrics.execution_time,
            weights=weights,
            metadata=performance_metrics,
            warnings=warnings,
        )
    except Exception as e:
        logger.error(f"Prompt backtest error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
