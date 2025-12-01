from steam_analysis.database.facade import DbFacade
from steam_analysis.proccessors.clustering_game_proccessor import ClusteringGameProcessor


class ProcessedDataProvider: # типа фасад

    def __init__(self):
        self.database_facade = DbFacade()
        self.clustering_game_proccesor = ClusteringGameProcessor()

    # region Providing data for simple-visualisation
    def get_games_by_categories(self):
        data = self.database_facade.get_games_by_categories()
        return data

    def get_games_by_genres(self):
        data = self.database_facade.get_games_by_genres()
        return data

    # endregion
