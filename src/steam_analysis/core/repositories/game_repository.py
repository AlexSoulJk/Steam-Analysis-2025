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

    def get_by_id(self, app_id: int, lang = None, **kwargs) -> Optional[GameDataAnalysisCreate]:
        """Получить игру по AppID"""
        url = f"{GameRepository.STORE_URL}/api/appdetails"
        params = {'appids': app_id}
        if lang:
            params['l'] = lang

        try:
            data = self.http_client.get(url, params=params)
            game_data = data.get(str(app_id), {'success': False})
            # TODO: Handle error !!
            if not game_data.get('success'):
                logger.warning(f"\n ❗️ Game {app_id} not found or failed to load")
                return None
            return self._parse_game_data(app_id, game_data['data'])
        except Exception as e:
            logger.error(f"\n ❗️ Error getting game {app_id}: {e}")
            return None

    def get_by_ids(self, ids: list[int], lang = None, **kwargs) -> Optional[List[GameDataAnalysisCreate]]:
        # url = f"{GameRepository.STORE_URL}/api/appdetails"
        # params = {'appids': ids}

        results = []
        for app_id in ids:
            game = self.get_by_id(app_id, lang, **kwargs)
            if game:
                results.append(game)
            else:
                logger.warning(f"\n ❗️ Game with AppID {app_id} could not be retrieved.")

        return results if results else None


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
            logger.error(f"\n ❗️Error getting game list: {e}")
            return []

    def _get_cached_app_list(self) -> List[dict]:
        """Получить кэшированный список приложений"""
        # Если кэш устарел или пустой, обновляем
        if self._full_app_list_cache is None:
            self._full_app_list_cache = self._fetch_app_list()
            logger.info(f"\n ℹ️ Cached app list with {len(self._full_app_list_cache)} items")

        return self._full_app_list_cache

    def _fetch_app_list(self) -> List[dict]:
        """Загрузить полный список приложений с API"""
        if self.resource_manager.is_resource_expired(ResourceCodes.GAME_LIST):
            url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamApps}/GetAppList/v2/"
            logger.info("\n ℹ️ Fetching full app list from Steam API...")
            response = self.http_client.get(url)
            apps = response.get('applist', {}).get('apps', [])
            self.resource_manager.save_resource(ResourceCodes.GAME_LIST, apps)
            logger.info(f"\n ℹ️ Retrieved {len(apps)} applications")
        else:
            apps = self.resource_manager.get_resource_data(ResourceCodes.GAME_LIST)

        return apps

    # TODO: дописать схему
    def get_schema(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Получить схему игры (достижения, статистика)"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamUserStats}/GetSchemaForGame/v2/"
        params = {'key': self.api_key,
                  'appid': app_id}
        
        try:
            data = self.http_client.get(url, params=params)
            schema_data = data.get('game', [])
            if not schema_data:
                logger.warning(f"\n ❗️ Schema for dame {app_id} not found or failed to load")
                return None
            return schema_data
        
        except Exception as e:
            logger.error(f"\n ❗️ Error getting schema for game {app_id}: {e}")
            return None

    # TODO: дописать схему
    def get_news(self, app_id: int) -> List[Dict[str, Any]]:
        """Получить новости об игре"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamNews}/GetNewsForApp/v2"
        params = {'appid': app_id}

        try:
            data = self.http_client.get(url, params=params)
            news_data = data.get('appnews', [])

            if not news_data:
                logger.warning(f"\n ❗️ News for dame {app_id} not found or failed to load")
                return None
            # TODO: дописать парсер для news
            # return self._parse_news_data(app_id, news_data['newsitems'], news_data['count'])
            return news_data['newsitems']
        
        except Exception as e:
            logger.error(f"\n ❗️ Error getting news for game {app_id}: {e}")
            return None
        
    # TODO: дописать схему
    def get_achiev_persentage(self, app_id: int) -> List[Dict[str, Any]]:
        """Получить глобальные проценты выполнения достижений для определённой игры"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamUserStats}/GetGlobalAchievementPercentagesForApp/v2"
        params = {'gameid': app_id}

        try:
            data = self.http_client.get(url, params=params)
            achiev_data = data.get('achievementpercentages', [])

            if not achiev_data:
                logger.warning(f"\n ❗️ Global achievement percentages for dame {app_id} not found or failed to load")
                return None
            # TODO: дописать парсер для achiev
            # return self._parse_news_data(app_id, news_data['newsitems'], news_data['count'])
            return achiev_data['achievements']
        
        except Exception as e:
            logger.error(f"\n ❗️ Error getting global achievement percentages for game {app_id}: {e}")
            return None
        
    # TODO: дописать схему
    # я так и не поняла, как тут отправить в запросе больше одной статистики :(
    def get_global_stats(self, app_id: int, count: int, names: List[str]) -> List[Dict[str, Any]]:
        """Получить проценты глобальной статистики для определённой игры"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamUserStats}/GetGlobalStatsForGame/v1"
        params = {'appid': app_id,
                  'count': count}
        
        if len(names) != count:
            logger.warning(f"\n ❗️ Ожидалось {count} элементов в names, но получено {len(names)}.")
            return None
        
        for i in range(count):
            params[f'name[{i}]'] = names[i]

        try:
            data = self.http_client.get(url, params=params)
            stats_data = data.get('response', [])

            if 'error' in stats_data:
                logger.warning(f"\n ❗️ Error getting global stats for game {app_id}: {stats_data.get('error')}")
                return None
            # TODO: дописать парсер для global_stats
            # return self._parse_news_data(app_id, news_data['newsitems'], news_data['count'])
            return stats_data
        
        except Exception as e:
            logger.error(f"\n ❗️ Error getting global stats for game {app_id}: {e}")
            return None
        
    # TODO: дописать схему
    def get_number_of_players(self, app_id: int) -> List[Dict[str, Any]]:
        """Получить общее число игроков, активных в данный момент в указанной игре"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamUserStats}/GetNumberOfCurrentPlayers/v1"
        params = {'appid': app_id}

        try:
            data = self.http_client.get(url, params=params)
            player_data = data.get('response', [])

            if not player_data:
                logger.warning(f"\n ❗️ Number of players for game {app_id} not found or failed to load")
                return None
            # TODO: дописать парсер для number_of_players
            # return self._parse_news_data(app_id, news_data['newsitems'], news_data['count'])
            return player_data['player_count']
        
        except Exception as e:
            logger.error(f"\n ❗️ Error getting global stats for game {app_id}: {e}")
            return None
        
    # TODO: дописать схему
    def get_reviews(self, app_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить отзывы об игре"""
        url = f"{self.STORE_URL}/appreviews/{app_id}"
        params = {
            'json': 1,
            'filter': 'recent',
            'language': 'all',
            'purchase_type': 'all',
            'num_per_page': limit
        }

        try:
            data = self.http_client.get(url, params=params)
            if not data.get('success', []):
                logger.warning(f"\n ❗️ Reviews for dame {app_id} not found or failed to load")
                return None
            # TODO: дописать парсер для reviews
            # return self._parse_news_data(app_id, news_data['reviews'], news_data['query_summary'])
            return data.get('reviews', [])
        
        except Exception as e:
            logger.error(f"\n ❗️ Error getting reviews for game {app_id}: {e}")
            return None



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