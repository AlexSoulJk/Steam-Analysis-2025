import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from datetime import datetime

from steam_analysis.config import analysis_db_path  # путь к analysis-db.sqlite
from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkCreate, GameAnalysisFromJson, \
    GameAnalysisChunkUpdate, GameAnalysisChunkForResponse
from steam_analysis.core.services.app_id_provider import AppIdProviderService
from steam_analysis.database.models.servicemodels import AnalysisChunk, GameDataAnalysis

from steam_analysis.config import analysis_db_path
from steam_analysis.core.schemas.game.service import GameDataAnalysisCreate, FillGameAnalysisChunk
from steam_analysis.database.services.game_analysis_preparer import GamePreparer
from steam_analysis.database.services.game_data_provider import GameAnalysisProvider

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


def safe_app_id(game_data) -> int:
    if game_data is None:
        return 0

    if isinstance(game_data, int):
        return game_data

    if hasattr(game_data, "app_id"):
        return getattr(game_data, "app_id") or 0

    game = getattr(game_data, "game", None)
    if game and hasattr(game, "app_id"):
        return getattr(game, "app_id") or 0

    return 0


class AnalysisDbFacade:
    """
    Фасад для работы с базой анализа (analysis-db).
    Управляет чанками и результатами парсинга.
    """

    def __init__(self):
        self.provider = None  # сервис провайдера app_id создаётся лениво
        self.data_game_preparer = GamePreparer()
        self.provider_service = GameAnalysisProvider()

    def _get_provider(self, session: Session) -> AppIdProviderService:
        if not self.provider:
            self.provider = AppIdProviderService(session)
        return self.provider

    def create_chunk_by_service(self, chunks: list[GameAnalysisChunkCreate],
                                games: list[list[GameAnalysisFromJson]]):

        with get_analysis_db() as session:
            self.data_game_preparer.create_chuncks(chunks, games, session)

    def create_chunk(self, app_ids: List[int], processed_by: Optional[str] = None) -> AnalysisChunk:
        """Создаем новый чанк для обработки"""
        chunk = AnalysisChunk(
            app_ids=app_ids,
            start_app_id=app_ids[0] if app_ids else None,
            end_app_id=app_ids[-1] if app_ids else None,
            processed_by=processed_by,
            status="pending",
            started_at=datetime.utcnow()
        )
        with get_analysis_db() as db:
            db.add(chunk)
            db.commit()
            db.refresh(chunk)
        return chunk

    def add_game_data(self, chunk_id: int, game_data: GameDataAnalysisCreate, status="success", error_log=None):
        """Добавляем результаты анализа конкретной игры в чанк"""

        app_id = safe_app_id(game_data)
        with get_analysis_db() as db:
            game_analysis = GameDataAnalysis(
                chunk_id=chunk_id,
                app_id=app_id,
                status=status,
                response_time=getattr(game_data, "response_time", None),
                error_log=error_log,
                processed=False
            )
            db.add(game_analysis)
            db.commit()
            db.refresh(game_analysis)
        return game_analysis

    def mark_chunk_complete(self, chunk_id: int):
        """Помечаем чанк как обработанный"""
        with get_analysis_db() as db:
            chunk = db.query(AnalysisChunk).filter(AnalysisChunk.id == chunk_id).first()
            if chunk:
                chunk.status = "success"
                chunk.completed = True
                chunk.finished_at = datetime.utcnow()
                db.commit()

    def get_next_pending_chunk(self) -> Optional[AnalysisChunk]:
        """Получаем следующий чанк для обработки"""
        with get_analysis_db() as db:
            return db.query(AnalysisChunk).filter(AnalysisChunk.status == "pending").order_by(AnalysisChunk.id).first()

    def get_next_pending_chunk_by_service(self, processor_name: str) -> Optional[GameAnalysisChunkForResponse]:
        """Получаем следующий чанк для обработки"""
        with get_analysis_db() as session:
            return GameAnalysisChunkForResponse.from_orm(
                self.provider_service.get_next_pending_chunk_by_processor_name(processor_name=processor_name,
                                                                               session=session))

    def get_last_upploaded_game(self) -> Optional[GameDataAnalysis]:
        with get_analysis_db() as session:
            return self.data_game_preparer.get_last_uploaded_game(session=session)
