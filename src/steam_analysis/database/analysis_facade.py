from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional

from steam_analysis.config import analysis_db_path

from steam_analysis.core.schemas.analysis.game import GameAnalysisChunkCreate, GameAnalysisFromJson, \
    GameAnalysisChunkUpdate, GameAnalysisChunkForResponse, GameAnalysisChunkForRequest
from steam_analysis.core.schemas.analysis.user import UserAnalysisChunkCreate, UserAnalysisFromJson, \
    UserAnalysisChunkUpdate, UserAnalysisChunkForResponse, UserAnalysisChunkForRequest

from steam_analysis.core.services.app_id_provider import AppIdProviderService

from steam_analysis.database.models.servicemodels import AnalysisChunk, GameDataAnalysis
from steam_analysis.database.models.serviceplayermodels import AnalysisUserChunk, UserDataAnalysis

from steam_analysis.core.schemas.game.service import UserDataAnalysisCreate, FillGameAnalysisChunk
from steam_analysis.core.schemas.player.service import PlayerDataAnalysisCreate, FillPlayerAnalysisChunk

from steam_analysis.database.services.game_analysis_preparer import GamePreparer
from steam_analysis.database.services.user_analysis_preparer import UserPreparer

from steam_analysis.database.services.game_data_provider import GameAnalysisProvider
from steam_analysis.database.services.user_data_provider import UserAnalysisProvider


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
        self.data_game_preparer = GamePreparer()
        self.data_user_preparer = UserPreparer()
        self.provider_game_service = GameAnalysisProvider()
        self.provider_user_service = UserAnalysisProvider()

    def create_chunk_by_service(self, chunks: list[GameAnalysisChunkCreate],
                                games: list[list[GameAnalysisFromJson]]):

        with get_analysis_db() as session:
            self.data_game_preparer.create_chuncks(chunks, games, session)

    def create_user_chunk_by_service(self, chunks: list[UserAnalysisChunkCreate],
                                     users: list[list[UserAnalysisFromJson]]):

        with get_analysis_db() as session:
            self.data_user_preparer.create_chuncks(chunks, users, session)
            # Коммит на уровне фасада выноси под самый конец работы.
            # За сессию должен быть один коммит.
            session.commit()

    def get_next_pending_chunk_by_service(self, processor_name: str) -> Optional[GameAnalysisChunkForResponse]:
        """Получаем следующий чанк для обработки"""
        with get_analysis_db() as session:
            return GameAnalysisChunkForResponse.from_orm(
                self.provider_game_service.get_next_pending_chunk_by_processor_name(processor_name=processor_name,
                                                                                    session=session))

    def mark_game_chunk_complete(self, chunk: GameAnalysisChunkForRequest):
        with get_analysis_db() as session:
            return self.data_game_preparer.mark_game_chunk_complete(chunk, session=session)

    def mark_user_chunk_complete(self, chunk: UserAnalysisChunkForRequest):
        with get_analysis_db() as session:
            return self.data_user_preparer.mark_user_chunk_complete(chunk, session=session)

    def get_last_upploaded_game(self) -> Optional[GameDataAnalysis]:
        with get_analysis_db() as session:
            return self.data_game_preparer.get_last_uploaded_game(session=session)

    def get_last_upploaded_user(self) -> Optional[str]:
        steam_id = None
        with get_analysis_db() as session:
            user = self.data_user_preparer.get_last_uploaded_user(session=session)
            if user:
                steam_id = user.steam_id
        return steam_id
