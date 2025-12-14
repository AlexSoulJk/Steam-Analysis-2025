from .base_worker import BaseWorker
from typing import Dict
import sys
import os

# Добавляем путь к проекту для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


class SteamAnalysisWorker(BaseWorker):
    """Воркер для работы с Steam API"""

    def __init__(self, node_id: str, master_host: str, master_port: int,
                 steam_api_key: str, host: str = "0.0.0.0", port: int = 5001):
        super().__init__(node_id, master_host, master_port, host, port)
        self.steam_api_key = steam_api_key
        self.steam_facade = None

        # Ленивая инициализация фасада
        self._init_steam_facade()

    def _init_steam_facade(self):
        """Инициализация Steam фасада (ленивая загрузка)"""
        try:
            from steam_analysis.core.client.steamclient import SteamAnalysisFacade
            self.steam_facade = SteamAnalysisFacade(self.steam_api_key)
            print(f"Steam facade initialized for worker {self.node_id}")
        except ImportError as e:
            print(f"Error importing SteamAnalysisFacade: {e}")
            self.steam_facade = None

    def process_task(self, task_data: Dict) -> Dict:
        """Обработка задачи Steam API"""
        if not self.steam_facade:
            self._init_steam_facade()
            if not self.steam_facade:
                raise RuntimeError("Steam facade not initialized")

        task_type = task_data.get("task_type")
        data = task_data.get("data", {})

        print(f"Worker {self.node_id} processing {task_type}")

        try:
            if task_type == "get_game_analysis_list":
                result = self.steam_facade.get_game_analysis_list(data)
                return {
                    "data_chunk": result.data_chunk,
                    "data_for_analysis_db": result.data_for_analysis_db
                }

            elif task_type == "get_add_game_list":
                result = self.steam_facade.get_add_game_list(data)
                return {
                    "data_chunk": result.data_chunk,
                    "data_for_analysis_db": result.data_for_analysis_db
                }

            elif task_type == "get_player_data_bunch":
                result = self.steam_facade.get_player_data_bunch(
                    data.get("chunk"),
                    data.get("skip_friends", False)
                )
                return {
                    "data_chunk": result.data_chunk,
                    "data_for_analysis_db": result.data_for_analysis_db
                }

            elif task_type == "get_player_game_data_bunch":
                result = self.steam_facade.get_player_game_data_bunch(data.get("chunk"))
                return {
                    "data_chunk": result.data_chunk,
                    "data_for_analysis_db": result.data_for_analysis_db
                }

            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except Exception as e:
            print(f"Error in SteamAnalysisWorker {self.node_id}: {e}")
            raise