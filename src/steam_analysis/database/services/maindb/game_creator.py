from typing import Optional, List, Tuple, Dict

from sqlalchemy.orm import Session

from steam_analysis.core.schemas.game.service import UserDataAnalysisCreate
from steam_analysis.core.services.schema_morpher import SchemaMorpher
from steam_analysis.database.models import Game
from steam_analysis.database.repositories.game.category import CategoryRepository
from steam_analysis.database.repositories.game.genre import GenreRepository
from steam_analysis.database.repositories.game.platform import PlatformRepository
from steam_analysis.database.repositories.game.type import TypeRepository
from steam_analysis.database.repositories import GameRepository
from steam_analysis.database.support_models.game_creation import PreparedForGameCreation


class GameCreationService:

    def __init__(self):
        self.game_repos = GameRepository()
        self.categories = CategoryRepository()
        self.types = TypeRepository()
        self.platforms = PlatformRepository()
        self.genres = GenreRepository()

    def _prepare_data_for_game_creation(self,
                                        data_without_none: list[UserDataAnalysisCreate],
                                        session: Session) -> PreparedForGameCreation:
        types = list(map(lambda x: x.game.type, data_without_none))
        platforms = list(map(lambda x: x.platforms, data_without_none))
        genres = list(map(lambda x: x.genres, data_without_none))
        categories = list(map(lambda x: x.categories, data_without_none))

        platforms = self.platforms.bulk_get_or_create(platforms,
                                                      session=session)

        genres = self.genres.bulk_get_or_create(genres,
                                                session=session)

        categories = self.categories.bulk_get_or_create(categories,
                                                        session=session)

        types = self.types.bulk_get_or_create(types,
                                              session=session)

        return PreparedForGameCreation(categories=categories,
                                       genres=genres,
                                       types=types,
                                       platforms=platforms)

    def create_chunk_games(self, games_info_chunk: List[Optional[UserDataAnalysisCreate]],
                           session: Session) -> Tuple[list[Game], PreparedForGameCreation,
    Dict[int, UserDataAnalysisCreate]]:
        data_without_none = list(filter(lambda x: x is not None, games_info_chunk))
        dict_without_nons = {data_analys_schema.game.app_id: data_analys_schema for data_analys_schema in
                             data_without_none}
        prep_info = self._prepare_data_for_game_creation(data_without_none=data_without_none,
                                                         session=session)

        games_to_create = SchemaMorpher.game_create_from_http_to_database(
            games=list(map(lambda x: x.game, data_without_none)),
            types=prep_info.types)

        games = self.game_repos.create_bulk(games_to_create,
                                            session=session)

        return games, prep_info, dict_without_nons
