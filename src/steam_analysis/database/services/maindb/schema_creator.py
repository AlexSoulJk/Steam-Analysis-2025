from typing import Optional, List, Tuple, Dict

from sqlalchemy.orm import Session

from steam_analysis.core.schemas.game.service import SchemaCreate, AddInfo
from steam_analysis.core.services.schema_morpher import SchemaMorpher
from steam_analysis.database.models import Game
from steam_analysis.database.repositories import GameRepository
from steam_analysis.database.repositories.game.achiev import AchievRepository
# from steam_analysis.database.repositories.game.stat import StatsRepository
from steam_analysis.database.support_models.schema_creation import PreparedForSchemaCreation


class SchemaCreationService:

    def __init__(self):
        self.game_repos = GameRepository()
        self.achievs = AchievRepository()
        # self.stats = StatsRepository()x

    def create_chunk_schemas(self, schemas_chunk: List[Optional[SchemaCreate]],
                           session: Session) -> Tuple[list[Game], PreparedForSchemaCreation,
                            Dict[int, SchemaCreate]]:
        data_without_none = list(filter(lambda x: x is not None, schemas_chunk))
        dict_without_nons = {data_analys_schema.game_id: data_analys_schema for data_analys_schema in
                             data_without_none}

        created_achievements = self.achievs.create_bulk(dict_without_nons,
                                            session=session)

    def __check_user_game_created(self, data_list, session) -> \
            Tuple[Dict[str, int], List[str]]:

        unique_app_ids = list({data.app_id for data in data_list})

        no_created_games = []
        games_id = {}
        for app_id in unique_app_ids:
            game = self.game_repos.get_by_app_id(app_id=app_id, session=session)
            if game:
                games_id[app_id] = game.id
            else:
                no_created_games.append(app_id)

        return games_id, no_created_games

    def create_chunk_add_schemas(self, schemas_chunk: List[Optional[AddInfo]], session: Session):
        valid_games_add_data = [data for data in schemas_chunk if data is not None]

        if not valid_games_add_data:
            return

        all_detailes = []

        for data in valid_games_add_data:
            for owned in data.owned_games:
                all_schemas.append(owned)

        players_ids, games_ids, no_created_players, no_created_games = \
            self.__check_user_game_created(all_owned, session)
        data_without_none = list(filter(lambda x: x is not None, schemas_chunk))
        dict_without_nons = {data_analys_schema.game_id: data_analys_schema for data_analys_schema in
                             data_without_none}

        created_achievements = self.achievs.create_bulk(dict_without_nons,
                                            session=session)

