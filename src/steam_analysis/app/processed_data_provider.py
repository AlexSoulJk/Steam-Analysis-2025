from steam_analysis.database.facade import DbFacade
from steam_analysis.proccessors.clustering_game_proccessor import ClusteringGameProcessor


class ProcessedDataProvider: # ЭТО ФАСАД, ТУТ ВСЕ СЕРВИСЫ, РЕШАЮЩИЕ ЗАДАЧИ

    def __init__(self):
        # Services that process data
        self.clustering_game_proccesor = ClusteringGameProcessor()

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


    # только для кластеризации

    def get_game_clustering_data(self, type_id, limit):
        return self.clustering_game_proccesor.get_game_clustering_data(type_id=type_id, limit=limit
                                                                       )

    def get_2d_hist_data(self,x_field, y_field, x_bins, y_bins, min_review_count):
        return self.clustering_game_proccesor.get_2d_hist_data(x_field=x_field,
                                                               y_field=y_field,
                                                               x_bins=x_bins,
                                                               y_bins=y_bins,
                                                               type_id=1)

    def enhanced_histogram_data(self):
        return self.clustering_game_proccesor.enhanced_histogram_data()
    # endregion



