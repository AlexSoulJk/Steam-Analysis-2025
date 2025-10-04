import os

from steam_analysis.config import db_path
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk
from steam_analysis.database.repositories import GameRepository
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from steam_analysis.database.repositories.game.category import CategoryRepository
from steam_analysis.database.repositories.game.genre import GenreRepository
from steam_analysis.database.repositories.game.platform import PlatformRepository

# Для Windows абсолютного пути:
engine = create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    """Простой контекстный менеджер"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Или еще проще:
def get_db_session():
    """Просто возвращает сессию (нужно закрывать вручную)"""
    return SessionLocal()


class DbFacade:

    def __init__(self):
        self.game_repos = GameRepository()
        self.categories = CategoryRepository()
        # self.types = TypeRepository()
        self.platforms = PlatformRepository()
        self.genres = GenreRepository()
        # self.price = PriceHistory()

    def create_games(self, games_info_chunk: FillGameAnalysisChunk):
        with get_db() as session:
            self.platforms.create_bulk(list(map(lambda x: x.platforms, games_info_chunk.data_chunk)))
            # self.types.create_bulk(list(map(lambda x: x.types, games_info_chunk.data_chunk)))
            self.genres.create_bulk(list(map(lambda x: x.genres, games_info_chunk.data_chunk)))
            # self.price.create_bulk(list(map(lambda x: x)))
            self.categories.create_bulk(list(map(lambda x: x.categories, games_info_chunk.data_chunk)))
            self.game_repos.create_bulk(list(map(lambda x: x.game, games_info_chunk.data_chunk)), session=session)

    def get_last_upploaded_game(self):
        with get_db() as session:
            return self.game_repos.get_last_uploaded_game(session=session)
