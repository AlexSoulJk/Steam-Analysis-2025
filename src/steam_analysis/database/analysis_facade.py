from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional

import datetime
from steam_analysis.config import analysis_db_path

from steam_analysis.core.schemas import GameShortInfo, PlayerShortInfo
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

from steam_analysis.core.services.fastlogger import setup_logger
analysis_engine = create_engine(f"sqlite:///{analysis_db_path}")
AnalysisSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=analysis_engine)


@contextmanager
def get_analysis_db():
    """Контекстный менеджер для analysis-db"""
    db = AnalysisSessionLocal()
    try:
        yield db
        # db.rollback()
        db.commit()  # while testing with facade can be commented and up string need to uncommented for base safe
    except Exception as e:
        print(e)
        db.rollback()
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

    def update_chunk_by_service(self, games: List[GameShortInfo]):
        with get_analysis_db() as session:
            updated_time = datetime.datetime.now()
            exist_games = self.data_game_preparer.get_exist_games(games, session)
            exist_games_ids = list(exist_games.keys())

            chunks_ids = [game.chunk_id for game in exist_games.values()]
            chunks = self.data_game_preparer.chunk_repo.get_chunks_by_ids(chunks_ids, session)
            for chunk in chunks:
                chunk.status = "pending"
                chunk.updated_at = updated_time

            logger = setup_logger("update_games_strategy")
            for game in games:
                if game.app_id not in exist_games_ids:
                    logger.warning(f"Игра с app_id = {game.app_id} не существует!")
                else:
                    game.status = "pending"
                    game.updated_at = updated_time

    def create_user_chunk_by_service(self,
                                     users: list[UserAnalysisFromJson], processor_name: str):
        # chunks: list[UserAnalysisChunkCreate], # cуда пользователей и создаем чанкееее
        with get_analysis_db() as session:
            # self.data_user_preparer.create_chuncks(chunks, users, session)
            self.data_user_preparer.create_users(users, processor_name, session)
            # Коммит на уровне фасада выноси под самый конец работы.
            # За сессию должен быть один коммит.
            # session.commit()

    def update_user_chunk_by_service(self,
                                     users: list[PlayerShortInfo]):
        with get_analysis_db() as session:
            updated_time = datetime.datetime.now()
            steam_ids = [user.steam_id for user in users]
            exist_users = self.data_user_preparer.user_model_repo.get_existing_by_steam_ids(steam_ids, session)
            exist_users_ids = list(exist_users.keys())

            chunks_ids = [user.chunk_id for user in exist_users.values()]
            chunks = self.data_user_preparer.chunk_repo.get_chunks_by_ids(chunks_ids, session)
            for chunk in chunks:
                chunk.status = "pending"
                chunk.updated_at = updated_time

            logger = setup_logger("update_users_strategy")
            for user in users:
                if user.steam_id not in exist_users_ids:
                    logger.warning(f"Пользователь со steam_id = {user.steam_id} не существует!")
                else:
                    user.status = "pending"
                    user.updated_at = updated_time

    def get_exist_games(self, games: List[GameShortInfo]):
        # chunks: list[UserAnalysisChunkCreate], # cуда пользователей и создаем чанкееее
        with get_analysis_db() as session:
            # self.data_user_preparer.create_chuncks(chunks, users, session)
            return self.data_game_preparer.get_exist_games(games, session)


    # region Next Pending Chunk
    def get_next_pending_chunk_by_service(self, processor_name: str) -> Optional[GameAnalysisChunkForResponse]:
        """Получаем следующий чанк для обработки"""
        with get_analysis_db() as session:
            return GameAnalysisChunkForResponse.from_orm(
                self.provider_game_service.get_next_pending_chunk_by_processor_name(processor_name=processor_name,
                                                                                    session=session))

    def get_next_pending_user_chunk_by_service(self, processor_name: str) -> Optional[
        UserAnalysisChunkForResponse]:  # aaaaaaaaaaaaaaaaaaaaaaaaaaa
        """Получаем следующий чанк для обработки"""
        with get_analysis_db() as session:
            return UserAnalysisChunkForResponse.from_orm(
                self.provider_user_service.get_next_pending_chunk_by_processor_name(processor_name=processor_name,
                                                                                    session=session))

    # endregion
    def get_next_part_chunk_by_service(self, processor_name: str) -> Optional[GameAnalysisChunkForResponse]:
        """Получаем следующий чанк для обработки"""
        with get_analysis_db() as session:
            updated_chunk = self.provider_game_service.get_next_part_chunk_by_processor_name(
                processor_name=processor_name,
                session=session)

            # Создаем схему только с нужными полями
            return GameAnalysisChunkForResponse(id=updated_chunk.id,
                                                status=updated_chunk.status,
                                                games=updated_chunk.in_progress_games,
                                                response_time=updated_chunk.response_time)

    def get_next_user_part_chunk_by_service(self, processor_name: str) -> Optional[UserAnalysisChunkForResponse]:
        """Получаем следующий чанк для обработки"""
        with get_analysis_db() as session:
            updated_chunk = self.provider_user_service.get_next_part_chunk_by_processor_name(
                processor_name=processor_name,
                session=session)

            return UserAnalysisChunkForResponse.from_orm(updated_chunk)

    # region Next Partial Success

    # endregion
    def mark_game_chunk_complete(self, chunk: GameAnalysisChunkForRequest):
        with get_analysis_db() as session:
            return self.data_game_preparer.mark_game_chunk_complete(chunk, session=session)

    def mark_user_chunk_complete(self, chunk: UserAnalysisChunkForRequest):
        with get_analysis_db() as session:
            return self.data_user_preparer.mark_user_chunk_complete(chunk, session=session)

    def get_last_upploaded_game(self) -> Optional[int]:
        with get_analysis_db() as session:
            tmp = self.data_game_preparer.get_last_uploaded_game(session=session)
            return tmp.app_id if tmp else None

    def get_last_upploaded_user(self) -> Optional[str]:
        steam_id = None
        with get_analysis_db() as session:
            user = self.data_user_preparer.get_last_uploaded_user(session=session)
            if user:
                steam_id = user.steam_id
        return steam_id

    def get_users_count(self):
        with get_analysis_db() as session:
            return self.data_user_preparer.get_users_count(session=session)
