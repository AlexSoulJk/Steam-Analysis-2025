from steam_analysis.database.facade import DbFacade
from steam_analysis.proccessors.clustering_game_proccessor import ClusteringGameProcessor


class ProcessedDataProvider: # ЭТО ФАСАД, ТУТ ВСЕ СЕРВИСЫ, РЕШАЮЩИЕ ЗАДАЧИ

    def __init__(self):
        # Services that process data
        self.clustering_game_proccesor = ClusteringGameProcessor()

    # region Providing data for simple-visualisation
    def get_games_by_types(self):
        return self.clustering_game_proccesor.get_games_by_types()

    def get_games_by_genres(self):
        pass

    # endregion



