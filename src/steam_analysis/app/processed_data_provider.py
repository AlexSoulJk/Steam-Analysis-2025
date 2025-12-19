from steam_analysis.database.facade import DbFacade
from steam_analysis.proccessors.clustering_game_proccessor import ClusteringGameProcessor
from steam_analysis.proccessors.distribution_processor import DistribProcessor
from steam_analysis.proccessors.clustering_game_proccessor_external import ClusteringGameProcessorForFlourish
from steam_analysis.proccessors.friends_proccessor import FriendsProcessor
from steam_analysis.proccessors.geo_game_proccesor import GeoProccessor



from typing import List


class ProcessedDataProvider: # ЭТО ФАСАД, ТУТ ВСЕ СЕРВИСЫ, РЕШАЮЩИЕ ЗАДАЧИ

    def __init__(self):
        # Services that process data
        self.clustering_game_proccesor = ClusteringGameProcessor()
        self.visualisation_game_proccesor = DistribProcessor()
        self.clustering_game_proccesor_for_external = ClusteringGameProcessorForFlourish()
        self.geo_coordinate_proccessor = GeoProccessor()
        self.friends_proccessor = FriendsProcessor()


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

    def get_categories_dynamics(self,
                                n_columns: int = 10,
                                time_period: str = "yearly",
                                years_back: int = 5
                                ):
        try:
            result = self.visualisation_game_proccesor.get_categories_dynamics(
                n=n_columns,
                time_period=time_period,
                years_back=years_back
            )

            if result:
                print(f"DataProvider: Динамика по {len(result.ticks)} категориям")
                if result.values:
                    print(f"  Временных точек: {len(result.values[0])}")
                    for i in range(min(3, len(result.ticks))):
                        print(f"  {result.ticks[i]}: {result.values[i][:5]}...")

            return result

        except Exception as e:
            print(f"DataProvider ошибка (динамика категорий): {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_genres_dynamics(self,
                            n_columns: int = 10,
                            time_period: str = "yearly", years_back: int = 5):
        try:
            result = self.visualisation_game_proccesor.get_genres_dynamics(
                n=n_columns,
                time_period=time_period,
                years_back=years_back
            )
            if result:
                print(f"DataProvider: Динамика по {len(result.ticks)} жанрам")

            return result

        except Exception as e:
            print(f"DataProvider ошибка (динамика жанров): {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_genre_by_price(self, n_columns: int = 40):
        return self.visualisation_game_proccesor.get_price_distribution_by_genre(n=n_columns)

    def get_category_by_price(self, n_columns: int = 40):
        return self.visualisation_game_proccesor.get_price_distribution_by_category(n=n_columns)


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

    def get_geo_games(self, game_limit):
        return self.geo_coordinate_proccessor.get_games_by_geo(game_limit)

    def get_friends_by_games(self, steam_id: str):
        return self.friends_proccessor.get_friends_by_games(steam_id)


