from pathlib import Path
import json
from typing import List
from steam_analysis.core.client.steamclient import SteamAnalysisFacade
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk
from steam_analysis.core.services.game_analysis_creator import GameAnalysisCreator
from steam_analysis.core.services.user_analysis_creator import UserAnalysisCreator
from steam_analysis.database.analysis_facade import AnalysisDbFacade
from steam_analysis.database.facade import DbFacade
from steam_analysis.loader_test_data import default_loader
from steam_analysis.resourcemanager.manager import ResourceManager
from steam_analysis.resourcemanager.resources.codes import ResourceCodes
from steam_analysis.saver_test_data import default_saver


class AppMediator:

    def __init__(self, steam_api_key: str,
                 processor_name: str = "Test"):
        self.processor_name = processor_name
        self.steam_facade = SteamAnalysisFacade(steam_api_key)
        self.database_facade = DbFacade()
        self.analysis_service = AnalysisDbFacade()
        self.game_analysis_creator = GameAnalysisCreator()
        self.user_analysis_creator = UserAnalysisCreator()
        self.resource_manager = ResourceManager()

    # region Fill analysis-db.db

    def fill_analysis_game(self):
        last_game = self.analysis_service.get_last_upploaded_game()
        start_app_id = self.steam_facade.get_first_app_id() if last_game is None else last_game.app_id
        data_for_create = self.game_analysis_creator.get_game_analysis_data_for_create_from_resource(start_app_id)
        # default_saver.save_fill_game_analysis_butch_chunck(data_for_create)
        self.analysis_service.create_chunk_by_service(*data_for_create)

    def fill_analysis_user(self):
        last_steam_id = self.analysis_service.get_last_upploaded_user()
        data_for_create = self.user_analysis_creator.get_user_analysis_data_for_create_from_resource(last_steam_id=last_steam_id,
                                                                                                     user_resource=self.resource_manager.get_resource(ResourceCodes.USER_LIST))
        # self.analysis_service.create_user_chunk_by_service(data_for_create)

    # endregion

    # region Fill steam-analysis.db
    def create_game(self,
                    chunk_size: int = 10):
        # Получаем последний загруженный app_id
        chunk_for_create = self.analysis_service.get_next_pending_chunk_by_service(self.processor_name)
        # Получаем данные через Steam API
        fill_butch = self.steam_facade.get_game_analysis_list(chunk_for_create)
        # Сохранение chunk игр в JSON
        default_saver.save_fill_game_batch(fill_butch)
        # Load chunk from JSON
        # fill_butch = default_loader.load_fill_game_batch(filename="games_chunk_2025110306.json")
        # self.database_facade.create_games(fill_butch.data_chunk)
        # Завершаем чанк
        self.analysis_service.mark_game_chunk_complete(fill_butch.data_for_analysis_db)

    def create_user(self,
                    chunk_size: int = 10):
        fill_butch = default_loader.load_fill_user_batch(filename="players_20251020_100.json")
        # self.database_facade.create_users(fill_butch.data_chunk)
        # Завершаем чанк
        self.analysis_service.mark_user_chunk_complete(fill_butch.data_for_analysis_db)

    def create_time_game_butch(self):
        with open('test_data/games_30_130_20251006.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        app_ids = [item['game']['app_id'] for item in data['data_chunk'] if item is not None]

        print(app_ids)

        fill_butch = self.steam_facade.get_game_timed_data(app_ids)
        default_saver.save_fill_game_timed_data(fill_butch)
        pass

    def create_player_butch(self, steam_ids: List[str]):
        fill_butch = self.steam_facade.get_player_data_bunch(steam_ids)
        default_saver.save_fill_player_butch(fill_butch)

    def create_player_game_butch(self, steam_ids: List[str]):
        fill_butch = self.steam_facade.get_player_time_data_bunch(steam_ids)
        default_saver.save_fill_player_game_butch(fill_butch)
    # endregion
