from typing import List, Tuple

from steam_analysis.database.facade import get_db
from steam_analysis.proccessors.clustering_game_proccessor import ClusteringGameProcessor


class ClusteringGameProcessorForFlourish(ClusteringGameProcessor):

    def __init__(self):
        super().__init__()

    def get_games_by_types(self) -> List[Tuple[str, int]]:
        with get_db() as session:
            types = self.game_type_repo.get_multi(session=session)
            values = {type.description: self.game_repo.count(session=session, filters={"type_id": type.id})
                      for type in types}

        return list(values.items())
