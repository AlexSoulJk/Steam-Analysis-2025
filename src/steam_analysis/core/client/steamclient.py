from typing import Optional, Dict, Any, List
from ...core.dependencies.basehttp import RequestsClient, RequestsWithDelayClient
from ..repositories.player_repository import PlayerRepository
from ..repositories.game_repository import GameRepository
from ..services.player_service import PlayerService
from ..services.game_service import GameService


class SteamAnalysisFacade:
    """Фасад для удобной работы со Steam API"""

    def __init__(self, api_key: str):
        # Инициализация репозиториев
        self.player_repo = PlayerRepository(RequestsClient(), api_key)
        self.game_repo = GameRepository(RequestsWithDelayClient(delay=0.5), api_key)

        # Инициализация сервисов
        self.player_service = PlayerService(self.player_repo, self.game_repo)
        self.game_service = GameService(self.game_repo)


    def get_first_app_id(self):
        return self.game_service.get_first_app_id()

    # Player methods
    def get_player(self, steam_id: str) -> Optional[Dict[str, Any]]:
        return self.player_repo.get_by_id(steam_id)

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

    # Game methods
    def get_game(self, app_id: int, lang = None) -> Optional[Dict[str, Any]]:
        return self.game_repo.get_by_id(app_id, lang)

    def get_game_list(self, app_ids: list[int], lang = None,) -> Optional[List[Dict[str, Any]]]:
        return self.game_repo.get_by_ids(app_ids, lang)
    
    def get_schema(self, app_id: int) -> Optional[List[Dict[str, Any]]]:
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

    def analyze_game(self, app_id: int) -> Optional[Dict[str, Any]]:
        return self.game_service.get_game_analysis(app_id)

    def get_game_analysis_list(self, app_id: int, chunck_size: int):
        return self.game_service.get_game_analysis_list(app_id, chunck_size)

    def get_game_timed_data(self, app_ids: list[int]):
        return self.game_service.get_game_timed_data(app_ids)

    def get_game_reviews(self, app_id: int, limit: int = 100):
        return self.game_repo.get_reviews(app_id, limit)