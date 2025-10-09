from pathlib import Path

from steam_analysis.core.client.steamclient import SteamAnalysisFacade
from steam_analysis.database.facade import DbFacade
from steam_analysis.loader_test_data import default_loader
from steam_analysis.saver_test_data import default_saver


class AppMediator:

    def __init__(self, steam_api_key: str):
        self.steam_facade = SteamAnalysisFacade(steam_api_key)
        self.database_facade = DbFacade()

    def create_game(self, chunk_size: int = 10):
        # Main game filling case
        game = self.database_facade.get_last_upploaded_game()
        start_app_id = self.steam_facade.get_first_app_id() if game is None else game.app_id
        fill_butch = self.steam_facade.get_game_analysis_list(start_app_id, chunk_size)
        # fill_butch = default_loader.load_fill_game_batch(Path("games_30_130_20251006.json"))
        # default_saver.save_fill_game_batch(fill_butch)
        print("fill_butch: ", fill_butch)
        self.database_facade.create_games(fill_butch)