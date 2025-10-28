from pathlib import Path
import json
from typing import List
from steam_analysis.core.client.steamclient import SteamAnalysisFacade
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk
from steam_analysis.core.services.game_analysis_creator import GameAnalysisCreator
from steam_analysis.database.analysis_facade import AnalysisDbFacade
from steam_analysis.database.facade import DbFacade
from steam_analysis.loader_test_data import default_loader
from steam_analysis.saver_test_data import default_saver


class AppMediator:

    def __init__(self, steam_api_key: str,
                 processor_name: str = "Test"):
        self.processor_name = processor_name
        self.steam_facade = SteamAnalysisFacade(steam_api_key)
        self.database_facade = DbFacade()
        self.analysis_service = AnalysisDbFacade()
        self.game_analysis_creator = GameAnalysisCreator()


    def fill_analysis_game(self):
        last_game = self.analysis_service.get_last_upploaded_game()
        start_app_id = self.steam_facade.get_first_app_id() if last_game is None else last_game.app_id
        data_for_create = self.game_analysis_creator.get_game_analysis_data_for_create_from_resource(start_app_id)
        # default_saver.save_fill_game_analysis_butch_chunck(data_for_create)
        self.analysis_service.create_chunk_by_service(*data_for_create)

    # region Fill steam-analysis.db
    def create_game(self,
                    chunk_size: int = 10):
        # Получаем последний загруженный app_id
        chunk_for_create = self.analysis_service.get_next_pending_chunk_by_service(self.processor_name)

        # Получаем данные через Steam API
        fill_butch = self.steam_facade.get_game_analysis_list(chunk_for_create)

        default_saver.save_fill_game_batch(fill_butch)
        
        # Сохраняем в аналитической базе и фильтруем успешные игры для основной базы
        # successful_games = []
        # for game_data in fill_butch.data_chunk:
        #     if game_data is None:
        #         continue
        #     try:
        #         self.analysis_service.add_game_data(chunk.id, game_data)
        #         successful_games.append(game_data)  # только успешные
        #     except Exception as e:
        #         # Записываем ошибку в аналитическую базу
        #         self.analysis_service.add_game_data(
        #             chunk.id, game_data, status="failed", error_log=str(e)
        #         )
        #
        # # Сохраняем только успешные игры в основной базе
        # if successful_games:
        #     fill_chunk_successful = FillGameAnalysisChunk(
        #         start_app_id=start_app_id,
        #         end_app_id=start_app_id + chunk_size - 1,
        #         response_time=fill_butch.response_time,
        #         data_chunk=successful_games
        #     )
        #     self.database_facade.create_games(fill_chunk_successful)

        # Завершаем чанк
        # self.analysis_service.mark_chunk_complete(chunk.id)

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
