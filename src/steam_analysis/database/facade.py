import os
from operator import or_
from typing import Dict, List, Optional

from steam_analysis.config import db_path
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, GameDataAnalysisCreate
from steam_analysis.core.schemas.player.service import PlayerDataAnalysisCreate
from steam_analysis.core.services.schema_morpher import SchemaMorpher
from steam_analysis.database.models import Game, GameGenre, GameCategory, GamePlatform
from steam_analysis.database.repositories import GameRepository
from contextlib import contextmanager
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session

from steam_analysis.database.repositories.game.category import CategoryRepository
from steam_analysis.database.repositories.game.genre import GenreRepository
from steam_analysis.database.repositories.game.platform import PlatformRepository
from steam_analysis.database.repositories.game.type import TypeRepository
from steam_analysis.database.services.maindb.game_creator import GameCreationService
from steam_analysis.database.services.maindb.game_provider import GameProviderService
from steam_analysis.database.services.maindb.game_relations_creator import GameRelationsCreationService
from steam_analysis.database.services.maindb.player_creator import PlayerCreationService
from steam_analysis.database.services.maindb.player_relations_creator import PlayerRelationsCreationService
from steam_analysis.database.support_models.game_creation import PreparedForGameCreation

# Для Windows абсолютного пути:
engine = create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    """Простой контекстный менеджер"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(e)
        db.rollback()
    finally:
        db.close()


# Или еще проще:
def get_db_session():
    """Просто возвращает сессию (нужно закрывать вручную)"""
    return SessionLocal()


class DbFacade:

    def __init__(self):
        self.game_creation = GameCreationService()
        self.game_relations_creation = GameRelationsCreationService()
        self.game_provider = GameProviderService()
        self.player_creation = PlayerCreationService()
        self.player_relations_creation = PlayerRelationsCreationService()

    def create_games(self, games_info_chunk: List[Optional[GameDataAnalysisCreate]]):
        with get_db() as session:
            games, prep_info, dict_without_nons = self.game_creation.create_chunk_games(games_info_chunk,
                                                                     session)

            self.game_relations_creation.create_connections(prep_info=prep_info,
                                                            dict_without_none=dict_without_nons,
                                                            games=games,
                                                            session=session)

    def get_last_upploaded_game(self):
        with get_db() as session:
            return self.game_provider.get_last_upploaded_game(session=session)

    # region Gets Row data for simple-visualisation
    def get_games_by_categories(self):
        # USE self.game_provider
        pass

    def get_games_by_genres(self):
        # USE self.game_provider
        pass

    # endregion

    # for players
    def create_players(self, players_info_chunk: List[Optional[PlayerDataAnalysisCreate]]):
        with get_db() as session:
            players, prep_info, dict_without_nons = self.player_creation.create_chunk_players(players_info_chunk,
                                                                     session)

            self.player_relations_creation.create_connections(prep_info=prep_info,
                                                              dict_without_none=dict_without_nons,
                                                              players=players,
                                                              session=session)

            session.commit()
            # session.refresh()

