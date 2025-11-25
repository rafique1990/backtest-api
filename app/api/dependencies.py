from typing import Annotated

from fastapi import Depends

from app.backtest.engine import BacktestEngine
from app.services import get_data_service
from app.services.nlu_service import NluService


def get_backtest_engine():
    data_service = get_data_service()
    return BacktestEngine(data_service)


def get_nlu_service():
    return NluService()


EngineDependency = Annotated[BacktestEngine, Depends(get_backtest_engine)]
NluServiceDependency = Annotated[NluService, Depends(get_nlu_service)]
