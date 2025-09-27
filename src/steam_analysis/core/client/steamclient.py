from typing import Optional, Dict, Any
from ...core.dependencies.basehttp import RequestsClient, RequestsWithDelayClient
from ..repositories.player_repository import PlayerRepository
from ..repositories.game_repository import GameRepository
from ..services.player_service import PlayerService
from ..services.game_service import GameService


class SteamAnalysisFacade:
    """Фасад для удобной работы со Steam API"""

    def __init__(self, api_key: str):
        http_client = RequestsClient()

        # Инициализация репозиториев
        self.player_repo = PlayerRepository(http_client, api_key)
        self.game_repo = GameRepository(RequestsWithDelayClient(delay=0.5), api_key)

        # Инициализация сервисов
        self.player_service = PlayerService(self.player_repo, self.game_repo)
        self.game_service = GameService(self.game_repo)

    # Player methods
    def get_player(self, steam_id: str) -> Optional[Dict[str, Any]]:
        return self.player_repo.get_by_id(steam_id)

    def get_player_full_profile(self, steam_id: str) -> Optional[Dict[str, Any]]:
        return self.player_service.get_player_profile(steam_id)

    def analyze_player(self, steam_id: str) -> Optional[Dict[str, Any]]:
        return self.player_service.analyze_gaming_preferences(steam_id)

    # Game methods
    def get_game(self, app_id: int) -> Optional[Dict[str, Any]]:
        return self.game_repo.get_by_id(app_id)

    def analyze_game(self, app_id: int) -> Optional[Dict[str, Any]]:
        return self.game_service.get_game_analysis(app_id)

    def get_game_reviews(self, app_id: int, limit: int = 100):
        return self.game_repo.get_reviews(app_id, limit)