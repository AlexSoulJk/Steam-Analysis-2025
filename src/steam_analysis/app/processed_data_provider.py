from steam_analysis.database.facade import DbFacade
from steam_analysis.proccessors.clustering_game_proccessor import ClusteringGameProcessor
from steam_analysis.proccessors.clustering_game_proccessor_external import ClusteringGameProcessorForFlourish
from typing import List


class ProcessedDataProvider: # ЭТО ФАСАД, ТУТ ВСЕ СЕРВИСЫ, РЕШАЮЩИЕ ЗАДАЧИ

    def __init__(self):
        # Services that process data
        self.clustering_game_proccesor = ClusteringGameProcessor()
        self.visualisation_game_proccesor = ClusteringGameProcessor()
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



    def get_categories_dinamics(self, categories: List[str] = None,
                                time_period: str = "yearly"):
        return self.clustering_game_proccesor.get_categories_dinamics(categories, time_period)

    def get_genres_dinamics(self, genres: List[str] = None,
                            time_period: str = "yearly"):
        return self.clustering_game_proccesor.get_genres_dinamics(genres, time_period)

    def get_genre_by_price(self, n_columns: int = 40):
        return self.clustering_game_proccesor.get_price_distribution_by_genre(n=n_columns)

    def get_category_by_price(self, n_columns: int = 40):
        return self.clustering_game_proccesor.get_price_distribution_by_category(n=n_columns)



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

    def get_games_by_types_for_flurish(self):
        return self.clustering_game_proccesor_for_external.get_games_by_types()


