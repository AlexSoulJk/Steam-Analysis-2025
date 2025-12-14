from steam_analysis.database.facade import DbFacade
from steam_analysis.proccessors.clustering_game_proccessor import ClusteringGameProcessor
from steam_analysis.proccessors.clustering_game_proccessor_external import ClusteringGameProcessorForFlourish


class ProcessedDataProvider: # ЭТО ФАСАД, ТУТ ВСЕ СЕРВИСЫ, РЕШАЮЩИЕ ЗАДАЧИ

    def __init__(self):
        # Services that process data
        self.clustering_game_proccesor = ClusteringGameProcessor()
        self.clustering_game_proccesor_for_external = ClusteringGameProcessorForFlourish()

    # region Providing data for simple-visualisation
    def get_games_by_types(self):
        return self.clustering_game_proccesor.get_games_by_types()

    def get_games_by_categories(self):
        return self.clustering_game_proccesor.get_games_by_categories()

    def get_games_release_by_season(self, mode):
        return self.clustering_game_proccesor.get_games_release_by_season(mode)

    def get_games_by_genres(self):
        return self.clustering_game_proccesor.get_games_by_genres()

    def get_games_by_categories_count(self):
        return self.clustering_game_proccesor.get_games_by_categories_count()

    # endregion

    def get_games_by_types_for_flurish(self):
        return self.clustering_game_proccesor_for_external.get_games_by_types()


