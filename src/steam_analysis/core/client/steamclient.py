from typing import Optional, Dict, Any, List

from ..schemas.analysis.game import GameAnalysisChunkForResponse
from ..schemas.analysis.user import UserAnalysisChunkForResponse
from ..schemas.game.service import FillGameAnalysisChunk
from ...core.dependencies.basehttp import RequestsClient, RequestsWithDelayClient
from ..repositories.player_repository import PlayerRepository
from ..repositories.game_repository import GameRepository
from ..services.player_service import PlayerService
from ..services.game_service import GameService


class SteamAnalysisFacade:
    """Фасад для удобной работы со Steam API"""

    def __init__(self, api_key: str):
        # Инициализация репозиториев
        self.player_repo = PlayerRepository(RequestsWithDelayClient(delay=0.5), api_key)
        self.game_repo = GameRepository(RequestsWithDelayClient(delay=0.5), api_key)

        # Инициализация сервисов
        self.player_service = PlayerService(self.player_repo, self.game_repo)
        self.game_service = GameService(self.game_repo)


    def get_first_app_id(self):
        return self.game_service.get_first_app_id()

    def get_all_app_ids(self) -> list[int]:
        return self.game_service.get_all_app_ids()

    # Player methods
    def get_player(self, steam_id: str) -> Optional[Dict[str, Any]]:
        return self.player_repo.get_by_id(steam_id)

    def get_players_ids_by_one(self, steam_id: str, depth: int = 1) -> Optional[List[str]]:
        return self.player_service.get_players_ids_by_one(steam_id)

    def get_players_info(self, steam_ids: List[str]) -> Optional[List[Any]]:
        return self.player_repo.get_by_ids(steam_ids)

    def get_player_full_profile(self, steam_id: str) -> Optional[Dict[str, Any]]:
        return self.player_service.get_player_profile(steam_id)

    def get_player_achievements_by_one_game(self, steam_id: str, app_id: str) -> List[Dict[str, Any]]:
        return self.player_repo.get_player_achievements(steam_id, app_id)

    def get_player_game_stats(self, steam_id: str, app_id: str) -> List[Dict[str, Any]]:
        return self.player_repo.get_player_game_stats(steam_id, app_id)

    def analyze_player(self, steam_id: str) -> Optional[Dict[str, Any]]:
        return self.player_service.analyze_gaming_preferences(steam_id)

    def get_player_data_bunch(self, chunk_procession: UserAnalysisChunkForResponse, flag: bool):
        return self.player_service.get_player_data_analysis(chunk_procession, flag)

    def get_player_for_steam_analys_filling(self, players_id: list[str]):
        if not players_id:
            return None
        tmp = list(set(players_id))
        if len(players_id) != len(tmp): print("Ouch steam_id for players has some duplicates")
        return self.player_service.get_player_for_steam_analys_filling(tmp)

    def get_player_game_data_bunch(self, chunk_procession: UserAnalysisChunkForResponse):
        return self.player_service.get_player_game_data_analysis(chunk_procession)

    # def get_player_time_data_bunch(self, steam_ids: list[str]):
    #     return self.player_service.get_player_game_data(steam_ids)

    # Game methods
    # def get_game(self, app_id: int, lang = None) -> Optional[Dict[str, Any]]:
    #     return self.game_repo.get_by_id(app_id, lang)

    def get_game_list(self, app_ids: list[int], lang = None,) -> Optional[List[Dict[str, Any]]]:
        return self.game_repo.get_by_ids(app_ids, lang)
    
    def get_schema_list(self, app_id: int) -> Optional[List[Dict[str, Any]]]:
        return self.game_repo.get_schema(app_id)

    def get_news(self, app_id: int) -> Optional[List[Dict[str, Any]]]:
        return self.game_repo.get_news(app_id)
    
    def get_achiev_persentage(self, app_id: int) -> Optional[List[Dict[str, Any]]]:
        return self.game_repo.get_achiev_persentage(app_id)
    
    def get_global_stats(self, app_id: int, count: int, names: List[str]) -> Optional[List[Dict[str, Any]]]:
        return self.game_repo.get_global_stats(app_id, count, names)
    
    def get_number_of_players(self, app_id: int) -> Optional[List[Dict[str, Any]]]:
        return self.game_repo.get_number_of_players(app_id)
    
    def get_reviews(self, app_id: int) -> Optional[List[Dict[str, Any]]]:
        return self.game_repo.get_reviews(app_id)

    def get_game_analysis_list(self, chunk_procession: GameAnalysisChunkForResponse) -> FillGameAnalysisChunk:
        return self.game_service.get_game_analysis_list(chunk_procession)
    
    def get_schema_list(self, chunk_procession: GameAnalysisChunkForResponse) -> FillGameAnalysisChunk:
        return self.game_service.get_schema_list(chunk_procession)

    def get_game_timed_data(self, app_ids: list[int]):
        return self.game_service.get_game_timed_data(app_ids)

    def get_game_reviews(self, app_id: int, limit: int = 100):
        return self.game_repo.get_reviews(app_id, limit)

