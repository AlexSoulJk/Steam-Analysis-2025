from typing import Optional, List, Tuple, Dict

from sqlalchemy.orm import Session

from steam_analysis.core.schemas.game.service import SchemaCreate
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

