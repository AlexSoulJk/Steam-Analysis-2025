from typing import Dict, List

from steam_analysis.core.schemas.game.game import GameFromHttp, GameCreate
from steam_analysis.database.models import GameType
from steam_analysis.core.schemas.player.player import PlayerFromHttp, PlayerCreate


class SchemaMorpher:
    @staticmethod
    def game_create_from_http_to_database(games: List[GameFromHttp],
                                          types: Dict[str, GameType]) -> List[GameCreate]:
        res = []
        for game in games:
            game_data = game.model_dump()
            type_name = game_data.pop('type')  # Убираем поле type
            game_type = types.get(type_name["description"])
            res.append(GameCreate(**game_data, type_id=game_type.id))

        return res

    @staticmethod
    def user_create_from_http_to_database(players: List[PlayerFromHttp]) -> List[PlayerCreate]:
        res = []
        for player in players:
            player_data = player.model_dump()
            res.append(PlayerCreate(**player_data))

        return res
