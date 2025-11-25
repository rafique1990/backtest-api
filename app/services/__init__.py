from app.core.config import settings
from app.db.duckdb_engine import DuckDBEngine
from app.services.local_data_service import LocalDataService
from app.services.s3_data_service import S3DataService


def get_data_service():
    db_engine = DuckDBEngine()

    if settings.STORAGE_BACKEND == "s3" and settings.S3_BUCKET:
        return S3DataService(db_engine)
    return LocalDataService(db_engine)
