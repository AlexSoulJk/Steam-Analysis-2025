from .base import BaseRepository
from typing import List, Optional, Dict, Any

from ..codes.steamservices import SteamServices
from ...core.dependencies.basehttp import HTTPClient


class GameRepository(BaseRepository):

    STORE_URL = "https://store.steampowered.com"
    API_STEAMPOWERED_URL = "https://api.steampowered.com"

    def __init__(self, http_client: HTTPClient, api_key: str):
        self.http_client = http_client
        self.api_key = api_key

    def get_by_id(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Получить игру по AppID"""
        url = f"{GameRepository.STORE_URL}/api/appdetails"
        params = {'appids': app_id}

        data = self.http_client.get(url, params=params)
        game_data = data.get(str(app_id), {})
        return game_data.get('data') if game_data.get('success') else None

    def get_schema(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Получить схему игры (достижения, статистика)"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamUserStats}/GetSchemaForGame/v2/"
        params = {'key': self.api_key,
                  'appid': app_id}

        return self.http_client.get(url, params=params)

    def get_reviews(self, app_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить отзывы об игре"""
        url = f"{self.store_url}/appreviews/{app_id}"
        params = {
            'json': 1,
            'filter': 'recent',
            'language': 'all',
            'purchase_type': 'all',
            'num_per_page': limit
        }

        data = self.http_client.get(url, params=params)
        return data.get('reviews', [])
