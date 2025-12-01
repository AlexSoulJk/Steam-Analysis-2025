from typing import Optional

from steam_analysis.database.facade import get_db
from steam_analysis.database.repositories import GameRepository
from steam_analysis.database.repositories.game.type import TypeRepository
from steam_analysis.proccessors.schemas.games import GamesByTypes


class ClusteringGameProcessor:  # ЭТО СЕРВИС: ПООБЩАЛСЯ С БАЗОЙ И СОБРАЛ ДАННЫЕ ДЛЯ КЛАСТЕРИЗАЦИИ И ОТДАЛ В ПРОВАЙДЕР (ФАСАД)

    def __init__(self):
        self.game_repo = GameRepository()
        self.game_type_repo = TypeRepository()

    def get_games_by_types(self) -> Optional[GamesByTypes]:
        ret = None
        with get_db() as session:
            types = self.game_type_repo.get_multi(session=session)
            ticks = list(map(lambda x: x.description, types))
            values = {type.description: self.game_repo.count(session=session, filters={"type_id": type.id})
                      for type in types}
            ret = GamesByTypes(ticks=ticks,
                               values=values)
        return ret

