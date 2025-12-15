from steam_analysis.database.facade import DbFacade
from steam_analysis.proccessors.clustering_game_proccessor import ClusteringGameProcessor
from steam_analysis.proccessors.clustering_game_proccessor_external import ClusteringGameProcessorForFlourish
from steam_analysis.proccessors.friends_proccessor import FriendsProcessor
from steam_analysis.proccessors.geo_game_proccesor import GeoProccessor





class ProcessedDataProvider: # ЭТО ФАСАД, ТУТ ВСЕ СЕРВИСЫ, РЕШАЮЩИЕ ЗАДАЧИ

    def __init__(self):
        # Services that process data
        self.clustering_game_proccesor = ClusteringGameProcessor()
        self.clustering_game_proccesor_for_external = ClusteringGameProcessorForFlourish()
        self.geo_coordinate_proccessor = GeoProccessor()
        self.friends_proccessor = FriendsProcessor()

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

    def get_geo_games(self, game_limit):
        return self.geo_coordinate_proccessor.get_games_by_geo(game_limit)

    def get_friends_by_games(self, steam_id: str):
        return self.friends_proccessor.get_friends_by_games(steam_id)


