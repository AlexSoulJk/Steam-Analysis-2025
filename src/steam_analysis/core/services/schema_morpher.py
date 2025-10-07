from typing import Dict, List

from steam_analysis.core.schemas.game.game import GameFromHttp, GameCreate
from steam_analysis.database.models import GameType


class SchemaMorpher:
    @staticmethod
    def game_create_from_http_to_database(games: List[GameFromHttp],
                                          types: Dict[str, GameType]) -> List[GameCreate]:
        res = []
        for game in games:
            game_data = game.model_dump()
            type_name = game_data.pop('type')  # Убираем поле type
            type_id = types.get(type_name)
            res.append(GameCreate(**game_data, type_id=type_id))

        return res
