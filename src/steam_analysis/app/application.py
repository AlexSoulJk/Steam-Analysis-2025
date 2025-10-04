from steam_analysis.core.client.steamclient import SteamAnalysisFacade
from steam_analysis.database.facade import DbFacade


class AppMediator:

    def __init__(self, steam_api_key: str):
        self.steam_facade = SteamAnalysisFacade(steam_api_key)
        self.database_facade = DbFacade()

    def create_game(self, chunk_size: int = 10):
        # Main game filling case
        game = self.database_facade.get_last_upploaded_game()
        start_app_id = self.steam_facade.get_first_app_id() if game is None else game.id
        self.database_facade.create_games(self.steam_facade.get_game_analysis_list(start_app_id, chunk_size))