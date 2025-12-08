from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from steam_analysis.core.schemas.player.service import PlayerDataAnalysisCreate
from steam_analysis.core.schemas.player.player import PlayerFromHttp
from steam_analysis.core.services.schema_morpher import SchemaMorpher
from steam_analysis.database.models import User
from steam_analysis.database.repositories import (
    PlayerRepository
)
from steam_analysis.database.support_models.player_creation import PreparedForPlayerCreation


class PlayerCreationService:
    """Сервис для создания игроков и связанных данных"""

    def __init__(self):
        self.player_repos = PlayerRepository()

    def create_chunk_players(self,
                             players_info_chunk: List[Optional[PlayerDataAnalysisCreate]],
                             session: Session) -> Tuple[List[User], List[PlayerDataAnalysisCreate]]:
        """Создать чанк игроков с связанными данными"""

        # Фильтруем None значения
        data_without_none = list(filter(lambda x: x is not None, players_info_chunk))
        dict_without_none = {data_analysis_schema.player.steam_id: data_analysis_schema
                             for data_analysis_schema in data_without_none}

        player_to_create = SchemaMorpher.user_create_from_http_to_database(
            players=list(map(lambda x: x.player, data_without_none)))

        players = self.player_repos.create_bulk(player_to_create, session=session)

        return players, data_without_none
