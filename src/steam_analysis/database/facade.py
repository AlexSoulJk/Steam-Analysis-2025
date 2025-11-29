import os
from operator import or_
from typing import Dict, List, Optional

from steam_analysis.config import db_path

from steam_analysis.core.schemas.player.playergame import OwnershipHttp, AchievementHttp, ReviewHttp, PlaytimeHttp

from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, UserDataAnalysisCreate, SchemaCreate

from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, UserDataAnalysisCreate
from steam_analysis.core.schemas.player.service import PlayerDataAnalysisCreate, PlayerGameDataAnalysisCreate
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

from steam_analysis.database.services.maindb.user_creator import UserCreationService
# from steam_analysis.database.services.maindb.user_provider import UserProviderService # ?????????/

from steam_analysis.database.services.maindb.game_relations_creator import GameRelationsCreationService
from steam_analysis.database.support_models.game_creation import PreparedForGameCreation
from steam_analysis.database.services.maindb.schema_creator import SchemaCreationService

from steam_analysis.database.services.maindb.player_creator import PlayerCreationService
from steam_analysis.database.services.maindb.player_relations_creator import PlayerRelationsCreationService
from steam_analysis.database.support_models.game_creation import PreparedForGameCreation
from steam_analysis.database.services.maindb.schema_creator import SchemaCreationService
# from steam_analysis.database.services.maindb.schema_relations_creator import SchemaRelationsCreationService

from steam_analysis.database.services.maindb.player_game_relations_creator import PlayerGameRelationsCreationService

# Для Windows абсолютного пути:
engine = create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    """Простой контекстный менеджер"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
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
        self.schema_creation = SchemaCreationService()
        # self.schema_relations_creation = SchemaRelationsCreationService()
        self.player_game_relations_creation = PlayerGameRelationsCreationService()

    def create_games(self, games_info_chunk: List[Optional[UserDataAnalysisCreate]]):
        with get_db() as session:
            games, prep_info, dict_without_nons = self.game_creation.create_chunk_games(games_info_chunk,
                                                                     session)

            self.game_relations_creation.create_connections(prep_info=prep_info,
                                                            dict_without_none=dict_without_nons,
                                                            games=games,
                                                            session=session)

    def create_schemas(self, schemas_chunk: List[Optional[SchemaCreate]]):
        with get_db() as session:
            schemas, prep_info, dict_without_nons = self.schema_creation.create_chunk_schemas(schemas_chunk,
                                                                                              session)

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
    def create_players(self, players_info_chunk: List[Optional[PlayerDataAnalysisCreate]]) -> List[str]:
        with get_db() as session:
            no_created_friends, players, prep_info, dict_without_nons = self.player_creation.create_chunk_players(
                players_info_chunk,
                session)
            session.flush()

            self.player_relations_creation.create_connections_friends(prep_info=prep_info,
                                                                      players=players,
                                                                      session=session)

            session.flush()
            return no_created_friends

    def create_players_game_relations(self, players_info_chunk: List[Optional[PlayerGameDataAnalysisCreate]]):
        # Фильтруем None значения
        with get_db() as session:
            try:
                no_created_players, no_created_games, no_success_players = \
                    self.player_game_relations_creation.create_connections(players_info_chunk, session)

            except Exception as e:
                raise

    def create_ownerships(self, ownerships_chunk: List[Optional[OwnershipHttp]], session: Session):
        no_created_ownership, no_created_players, no_created_games = self.player_game_relations_creation. \
            create_connections_ownership(session=session, ownership_data=ownerships_chunk)

        return no_created_ownership, no_created_players, no_created_games

    def create_achievements(self, achievements_chunk: List[Optional[AchievementHttp]], session: Session):
        no_created_achievements, no_created_players, no_created_games = self.player_game_relations_creation. \
            create_connections_achievements(session=session, achievements_data=achievements_chunk)

        return no_created_achievements, no_created_players, no_created_games

    def create_playtimes(self, playtimes_chunk: List[Optional[PlaytimeHttp]], session: Session):
        no_created_playtimes, no_created_players, no_created_games = self.player_game_relations_creation. \
            create_connections_playtimes(session=session, playtimes_data=playtimes_chunk)
        return no_created_playtimes, no_created_players, no_created_games

    def create_reviews(self, reviews_chunk: List[Optional[ReviewHttp]]):
        with get_db() as session:
            no_created_reviews, no_created_players, no_created_games = self.player_game_relations_creation.\
                create_connections_review(session=session, reviews_data=reviews_chunk)

            session.commit()
            # session.refresh()
            return no_created_reviews, no_created_players, no_created_games