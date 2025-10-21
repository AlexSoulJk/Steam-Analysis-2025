import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from steam_analysis.config import analysis_db_path  # путь к analysis-db.sqlite
from steam_analysis.core.services.app_id_provider import AppIdProviderService
from steam_analysis.database.models.servicemodels import AnalysisChunk, GameDataAnalysis

analysis_engine = create_engine(f"sqlite:///{analysis_db_path}")
AnalysisSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=analysis_engine)


@contextmanager
def get_analysis_db():
    """Контекстный менеджер для analysis-db"""
    db = AnalysisSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_analysis_session() -> Session:
    """Просто вернуть открытую сессию для ручного управления"""
    return AnalysisSessionLocal()


class AnalysisDbFacade:
    """
    Фасад для работы с базой анализа (analysis-db).
    Управляет чанками и результатами парсинга.
    """

    def __init__(self):
        # подключаем сервис провайдера app_id
        self.provider = None

    def _get_provider(self, session: Session) -> AppIdProviderService:
        if not self.provider:
            self.provider = AppIdProviderService(session)
        return self.provider

    def create_chunks_range(self, start_id: int, end_id: int, step: int = 100, by: str = "system"):
        """Создать чанки для диапазона app_id"""
        with get_analysis_db() as db:
            provider = self._get_provider(db)
            chunks = provider.create_chunks_by_range(start_id, end_id, step, processed_by=by)
            return [chunk.id for chunk in chunks]

    def create_chunks_list(self, app_ids: list[int], chunk_size: int = 100, by: str = "system"):
        """Создать чанки для произвольного списка"""
        with get_analysis_db() as db:
            provider = self._get_provider(db)
            chunks = provider.create_chunks_from_list(app_ids, chunk_size, processed_by=by)
            return [chunk.id for chunk in chunks]

    def get_next_chunk(self):
        """Выдать следующий доступный чанк"""
        with get_analysis_db() as db:
            provider = self._get_provider(db)
            return provider.get_next_chunk()

    def mark_chunk_completed(self, chunk_id: int, null_count=0, not_null_count=0, failed_count=0):
        """Пометить чанк как завершенный"""
        with get_analysis_db() as db:
            provider = self._get_provider(db)
            provider.mark_chunk_completed(chunk_id, null_count, not_null_count, failed_count)

    def mark_chunk_failed(self, chunk_id: int, error: str):
        """Пометить чанк как ошибочный"""
        with get_analysis_db() as db:
            provider = self._get_provider(db)
            provider.mark_chunk_failed(chunk_id, error)

    def add_game_result(self, chunk_id: int, app_id: int, stats: dict = None, achievements: dict = None):
        """Добавить запись об анализе игры"""
        with get_analysis_db() as db:
            provider = self._get_provider(db)
            return provider.add_game_analysis(chunk_id, app_id, stats, achievements)

    def log_game_analysis(self, chunk_id: int, app_id: int,
                          status: str = "success",
                          response_time: float = None,
                          genres=None, categories=None, platforms=None,
                          stats=None, achievements=None,
                          error_log: str = None,
                          session: Session = None):
        local = session or AnalysisSessionLocal()

        record = GameDataAnalysis(
            chunk_id=chunk_id,
            app_id=app_id,
            status=status,
            response_time=response_time,
            genres=genres,
            categories=categories,
            platforms=platforms,
            stats=stats,
            achievements=achievements,
            error_log=error_log,
        )
        local.add(record)
        local.commit()

        if session is None:
            local.close()
