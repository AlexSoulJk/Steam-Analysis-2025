import time
from datetime import datetime

from .base import BaseRepository
from typing import List, Optional, Dict, Any

from ..codes.steamservices import SteamServices
from ..parsers.json.steamapi.game import GameParser
from ..schemas import GameShortInfo, GameCategory
from ..schemas.game.service import GameDataAnalysisCreate
from ...core.dependencies.basehttp import HTTPClient

import logging

from ...resourcemanager.resources.codes import ResourceCodes

logger = logging.getLogger(__name__)


class GameRepository(BaseRepository):
    STORE_URL = "https://store.steampowered.com"
    API_STEAMPOWERED_URL = "https://api.steampowered.com"

    def __init__(self, http_client: HTTPClient, api_key: str):
        super().__init__()
        self.http_client = http_client
        self.api_key = api_key
        self._full_app_list_cache: Optional[Any] = None

    def get_by_id(self, app_id: int, **kwargs) -> Optional[GameDataAnalysisCreate]:
        """Получить игру по AppID"""
        url = f"{GameRepository.STORE_URL}/api/appdetails"
        params = {'appids': app_id}

        try:
            data = self.http_client.get(url, params=params)
            game_data = data.get(str(app_id), {'success': False})
            # TODO: Handle error !!
            if not game_data.get('success'):
                logger.warning(f"Game {app_id} not found or failed to load")
                return None

            return self._parse_game_data(app_id, game_data['data'])
        except Exception as e:
            logger.error(f"Error getting game {app_id}: {e}")
            return None

    def get_by_ids(self, ids: list[int], **kwargs) -> Optional[List[GameDataAnalysisCreate]]:
        url = f"{GameRepository.STORE_URL}/api/appdetails"
        params = {'appids': ids}
        # TODO: WRITE LOGIC
        pass
        # try:
        #     data = self.http_client.get(url, params=params)
        #     # game_data = data.get(str(app_id), {})
        #
        #     if not game_data.get('success'):
        #         logger.warning(f"Game {app_id} not found or failed to load")
        #         return None
        #
        #     return self._parse_game_data(app_id, game_data['data'])
        # except Exception as e:
        #     logger.error(f"Error getting game {app_id}: {e}")
        #     return None

    def get_game_list(self,
                      offset: int = 0,
                      size: int = 100) -> List[GameShortInfo]:
        """
        Получить пагинированный список всех игр из Steam

        Args:
            offset: Смещение для пагинации
            size: Количество игр для возврата

        Returns:
            List[GameShortInfo]: Список игр с базовой информацией
        """
        # TODO: Add pagination decorator
        try:
            full_list = self._get_cached_app_list()

            # Применяем пагинацию
            start_idx = offset
            end_idx = offset + size

            if start_idx >= len(full_list):
                return []

            paginated_games = full_list[start_idx:end_idx]

            return [
                GameShortInfo(app_id=game['appid'], name=game['name'])
                for game in paginated_games
            ]

        except Exception as e:
            logger.error(f"Error getting game list: {e}")
            return []

    def _get_cached_app_list(self) -> List[dict]:
        """Получить кэшированный список приложений"""
        # Если кэш устарел или пустой, обновляем
        if self._full_app_list_cache is None:
            self._full_app_list_cache = self._fetch_app_list()
            logger.info(f"Cached app list with {len(self._full_app_list_cache)} items")

        return self._full_app_list_cache

    def _fetch_app_list(self) -> List[dict]:
        """Загрузить полный список приложений с API"""
        if self.resource_manager.is_resource_expired(ResourceCodes.GAME_LIST):
            url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamApps}/GetAppList/v2/"
            logger.info("Fetching full app list from Steam API...")
            response = self.http_client.get(url)
            apps = response.get('applist', {}).get('apps', [])
            self.resource_manager.save_resource(ResourceCodes.GAME_LIST, apps)
            logger.info(f"Retrieved {len(apps)} applications")
        else:
            apps = self.resource_manager.get_resource_data(ResourceCodes.GAME_LIST)

        return apps

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

    def get_category_list(self) -> List[GameCategory]:
        # TODO: WRITE LOGIC
        pass

    def _parse_game_data(self, app_id: int, raw_data: Dict[str, Any]) -> GameDataAnalysisCreate:
        """Парсинг сырых данных в структурированный формат для анализа"""

        game_create_info = GameParser.extract_game_create_info(app_id, raw_data)
        genres = GameParser.extract_game_genres(raw_data)
        categories = GameParser.extract_categories(raw_data)
        platforms = GameParser.extract_platforms(raw_data)

        return GameDataAnalysisCreate(
            # Базовые идентификаторы
            game=game_create_info,
            genres=genres,
            categories=categories,
            platforms=platforms,
        )



    @staticmethod
    def _extract_content_info(data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение информации о контенте"""
        # Анализ категорий для определения особенностей геймплея
        categories = [cat['description'].lower() for cat in data.get('categories', [])]

        game_features = {
            'single_player': any('single' in cat for cat in categories),
            'multiplayer': any('multi' in cat for cat in categories),
            'coop': any('co-op' in cat or 'coop' in cat for cat in categories),
            'pvp': any('pvp' in cat or 'competitive' in cat for cat in categories),
            'mods_support': any('mod' in cat for cat in categories),
            'vr_support': any('vr' in cat for cat in categories),
        }

        return {
            'is_free': data.get('is_free', False),
            'achievements_count': len(data.get('achievements', [])),
            'controller_support': data.get('controller_support', 'none'),
            'platforms': data.get('platforms', {}),
            'game_features': game_features,
        }

    @staticmethod
    def _extract_commerce_info(data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение коммерческой информации"""
        price_overview = data.get('price_overview', {})

        return {
            'price_info': {
                'currency': price_overview.get('currency', 'USD'),
                'initial': price_overview.get('initial', 0),
                'final': price_overview.get('final', 0),
                'discount_percent': price_overview.get('discount_percent', 0),
                'is_free': data.get('is_free', False),
            }
        }

    @staticmethod
    def _extract_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение метрик популярности"""
        # Расчет процента положительных отзывов
        reviews = data.get('reviews', '')
        review_score = 0.0
        review_count = 0

        if reviews and 'positive' in reviews and 'total' in reviews:
            # Парсинг строки типа "Very Positive (12,345)"
            import re
            match = re.search(r'(\d+)%', reviews)
            if match:
                review_score = int(match.group(1)) / 100.0

            # Получение количества отзывов
            total_match = re.search(r'\(([\d,]+)\)', reviews)
            if total_match:
                review_count = int(total_match.group(1).replace(',', ''))

        return {
            'recommendations_count': data.get('recommendations', {}).get('total', 0),
            'metacritic_score': data.get('metacritic', {}).get('score'),
            'review_score': review_score,
            'review_count': review_count,
        }