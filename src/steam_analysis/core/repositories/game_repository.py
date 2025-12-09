import time
from datetime import datetime

from .base import BaseRepository
from typing import List, Optional, Dict, Any, Tuple

from ..codes.steamservices import SteamServices
from ..parsers.json.steamapi.game import GameParser
from ..schemas import GameShortInfo, GameCategory
from ..schemas.analysis.game import GameAnalysisUpdate, GameAnalysisResponse
from ..schemas.game.service import SchemaCreate, AchievDataAnalysisCreate, \
    UserDataAnalysisCreate, AchievDataAnalysisCreate, \
    PlayersDataAnalysisCreate, ReviewsDataAnalysisCreate, NewsDataAnalysisCreate, \
    AddInfo, AddDetails, Price
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

    def get_by_schema(self, game_for_response: GameAnalysisResponse, lang=None) -> Tuple[
        Optional[UserDataAnalysisCreate], GameAnalysisUpdate]:
        url = f"{GameRepository.STORE_URL}/api/appdetails"
        params = {'appids': game_for_response.app_id}

        error_log_message = ""
        status = ""  # TODO: REFACTOR DEFAULT STATUS
        request_model = None

        if lang:
            params['l'] = lang

        try:
            data = self.http_client.get(url, params=params)
            game_data = data.get(str(game_for_response.app_id)) or {'success': False}
            # TODO: Handle error !!

            if not game_data.get('success'):
                error_log_message = f"Game app_id: {game_for_response.app_id} not found or failed to load"
                status = "null_state"
                logger.warning(f"\n ❗️ {error_log_message}")
            else:
                status = "particle"
                request_model = self._parse_game_data(game_for_response.app_id,
                                                      game_data['data'])

        except Exception as e:
            status = "failed"
            error_log_message = f"Error getting game: {e}"
            logger.error(f"\n ❗❗️ {error_log_message}")

        return request_model, GameAnalysisUpdate.from_response_schema(response=game_for_response,
                                                                      error_log=error_log_message,
                                                                      status=status)

    def get_by_id(self, app_id: int, lang=None, **kwargs) -> Optional[UserDataAnalysisCreate]:
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
                logger.warning(f"\n ❗️ Game app_id: {app_id} not found or failed to load")
                return None
            return self._parse_game_data(app_id, game_data['data'])
        except Exception as e:
            logger.error(f"\n ❗️ Error getting game app_id:{app_id}: {e}")
            return None

    def get_by_ids(self, ids: list[int], lang=None, **kwargs) -> Optional[List[UserDataAnalysisCreate]]:
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

    def get_add_info(self, game: GameAnalysisResponse) -> \
            Tuple[Optional[AddInfo], GameAnalysisUpdate]:
        add_details, details_error_log_message, details_status, details_add_status = self.get_add_details(game)
        schema, schema_error_log_message, schema_status, schema_add_status = self.get_schema(game)
        achiev_persentage, achiev_error_log_message, achiev_status = self.get_achiev_persentage(game.app_id)
        reviews, reviews_error_log_message, reviews_status = self.get_reviews(game.app_id)

        request_model = AddInfo(
            game_id=game.app_id,
            add_details=add_details,
            schema_data=schema,
            achiev_persentage=achiev_persentage,
            review_info=reviews
        )

        error_log_message = details_error_log_message + " // " + schema_error_log_message \
                            + " // " + achiev_error_log_message + " // " + reviews_error_log_message

        status = "details_" + details_status
        if details_add_status:
            status += " without" + details_add_status + " // "

        status += "schema_" + schema_status
        if schema_add_status:
            status += " without" + schema_add_status + " // "

        status += "achiev_" + achiev_status + " // review_" + reviews_status

        return request_model, GameAnalysisUpdate.from_response_schema(response=game,
                                                                      error_log=error_log_message,
                                                                      status=status)

    def get_add_details(self, game: GameAnalysisResponse, lang=None) -> Tuple[Optional[AddDetails], str, str, str]:
        url = f"{GameRepository.STORE_URL}/api/appdetails"
        params = {'appids': game.app_id}

        error_log_message = ""
        status = ""  # TODO: REFACTOR DEFAULT STATUS
        add_status = ""
        request_model = None

        if lang:
            params['l'] = lang

        try:
            data = self.http_client.get(url, params=params)
            game_data = data.get(str(game.app_id), {'success': False})
            # TODO: Handle error !!

            if not game_data.get('success'):
                error_log_message = f"Game app_id: {game.app_id} not found or failed to load"
                status = "null_state"
                logger.warning(f"\n ❗️ {error_log_message}")
            else:
                status = "success"
                data = game_data['data']
                developers = data.get('developers', [])
                publishers = data.get('publishers', [])
                price_overview_data = data.get('price_overview', None)
                add_dev = ""
                add_pub = ""
                add_price = ""
                if not developers:
                    status = "particle"
                    add_dev = " developers"
                if not publishers:
                    status = "particle"
                    add_pub = " publishers"
                if not price_overview_data:
                    status = "particle"
                    add_price = " price"
                add_status = add_dev + add_pub + add_price

                request_model = self._parse_add_details_data(game.app_id, developers, publishers, price_overview_data)

        except Exception as e:
            status = "failed"
            error_log_message = f"Error getting game: {e}"
            logger.error(f"\n ❗❗️ {error_log_message}")

        return request_model, error_log_message, status, add_status

    def get_schema(self, game: GameAnalysisResponse) -> Tuple[Optional[SchemaCreate], str, str, str]:
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamUserStats}/GetSchemaForGame/v2/"
        params = {'key': self.api_key,
                  'appid': game.app_id}

        error_log_message = ""
        status = "particle"  # TODO: REFACTOR DEFAULT STATUS
        add_status = ""
        request_model = None

        try:
            data = self.http_client.get(url, params=params)
            schema_data = data.get('game', {})
            if not schema_data:
                error_log_message = f"Schema for game {game.app_id} not found or failed to load"
                status = "failed"
                add_status = " schema"
                logger.warning(f"\n ❗️ {error_log_message}")
                return None, error_log_message, status, add_status
            else:
                stats = schema_data['availableGameStats'].get('stats', [])
                achievs = schema_data['availableGameStats'].get('achievements', [])
                status = "success"
                if not stats:
                    status = "particle"
                    add_status = " stats"
                if not achievs:
                    status = "particle"
                    add_status = " achievs"
                request_model = self._parse_schema_data(game.app_id, schema_data['gameVersion'], stats, achievs)

        except Exception as e:
            status = "failed"
            logger.error(f"\n ❗️ Error getting schema for game {game.app_id}: {e}")
            return None, error_log_message, status, add_status

        return request_model, error_log_message, status, add_status

    def get_news(self, app_id: int) -> Optional[NewsDataAnalysisCreate]:
        """Получить новости об игре"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamNews}/GetNewsForApp/v2"
        params = {'appid': app_id}

        try:
            data = self.http_client.get(url, params=params)
            news_data = data.get('appnews', [])

            if not news_data:
                logger.warning(f"\n ❗️ News for dame {app_id} not found or failed to load")
                return None
            return self._parse_news_data(app_id, data)

        except Exception as e:
            logger.error(f"\n ❗️ Error getting news for game {app_id}: {e}")
            return None

    def get_achiev_persentage(self, app_id: int) -> Tuple[Optional[AchievDataAnalysisCreate], str, str]:
        """Получить глобальные проценты выполнения достижений для определённой игры"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamUserStats}/GetGlobalAchievementPercentagesForApp/v2"
        params = {'gameid': app_id}
        error_log_message = ""

        try:
            data = self.http_client.get(url, params=params)
            achiev_data = data.get('achievementpercentages', [])

            if not achiev_data:
                error_log_message = f"Global achievement percentages for dame {app_id} not found or failed to load"
                logger.warning(f"\n ❗️ {error_log_message}")
                status = "failed"
                return None, error_log_message, status
            status = "success"
            request_model = self._parse_achiev_data(app_id, data)

        except Exception as e:
            error_log_message = f"Error getting global achievement percentages for game {app_id}: {e}"
            logger.error(f"\n ❗️ {error_log_message}")
            return None, error_log_message, "failed"

        return request_model, error_log_message, status

    # TODO: дописать схему
    # 1) я так и не поняла, как тут отправить в запросе больше одной статистики :(
    # 2) у меня не получилось получить норм ответ без ошибки
    def get_global_stats(self, app_id: int, count: int, names: List[str]) -> Optional[List[Dict[str, Any]]]:
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

    def get_number_of_players(self, app_id: int) -> Optional[PlayersDataAnalysisCreate]:
        """Получить общее число игроков, активных в данный момент в указанной игре"""
        url = f"{GameRepository.API_STEAMPOWERED_URL}/{SteamServices.ISteamUserStats}/GetNumberOfCurrentPlayers/v1"
        params = {'appid': app_id}

        try:
            data = self.http_client.get(url, params=params)
            player_data = data.get('response', [])

            if not player_data:
                logger.warning(f"\n ❗️ Number of players for game {app_id} not found or failed to load")
                return None

            return self._parse_players_data(app_id, data)

        except Exception as e:
            logger.error(f"\n ❗️ Error getting global stats for game {app_id}: {e}")
            return None

    def get_reviews(self, app_id: int, limit: int = 100) -> Tuple[Optional[ReviewsDataAnalysisCreate], str, str]:
        """Получить отзывы об игре"""
        url = f"{self.STORE_URL}/appreviews/{app_id}"
        params = {
            'json': 1,
            'filter': 'recent',
            'language': 'all',
            'purchase_type': 'all',
            'num_per_page': limit
        }
        error_log_message = ""

        try:
            data = self.http_client.get(url, params=params)
            if not data.get('success', []):
                status = "failed"
                error_log_message = f"Reviews for dame {app_id} not found or failed to load"
                logger.warning(f"\n ❗️ {error_log_message}")
                return None, error_log_message, status

            status = "success"
            request_model = self._parse_reviews_data(app_id, data)

        except Exception as e:
            status = "failed"
            error_log_message = f"Error getting reviews for game {app_id}: {e}"
            logger.error(f"\n ❗️{error_log_message}")
            return None, error_log_message, status

        return request_model, error_log_message, status

    def get_category_list(self) -> List[GameCategory]:
        # TODO: WRITE LOGIC
        pass

    def _parse_game_data(self, app_id: int, raw_data: Dict[str, Any]) -> UserDataAnalysisCreate:
        """Парсинг сырых данных в структурированный формат для анализа"""

        game_create_info = GameParser.extract_game_create_info(app_id, raw_data)
        genres = GameParser.extract_game_genres(raw_data)
        categories = GameParser.extract_categories(raw_data)
        platforms = GameParser.extract_platforms(raw_data)

        return UserDataAnalysisCreate(
            # Базовые идентификаторы
            game=game_create_info,
            genres=genres,
            categories=categories,
            platforms=platforms,
        )

    def _parse_add_details_data(self, app_id: int, developers: List[Any], publishers: List[Any],
                                price_overview_data: Dict[str, Any]) -> AddDetails:

        if price_overview_data:
            price_overview = Price(
                game_id=app_id,
                currency=price_overview_data['currency'],
                initial=price_overview_data['initial'],
                final=price_overview_data['final'],
                discount_percent=price_overview_data['discount_percent'])
        else:
            price_overview = None

        return AddDetails(
            game_id=app_id,
            developers=developers,
            publishers=publishers,
            price_overview=price_overview
        )

    def _parse_schema_data(self, app_id: int, game_version: int, stats: List[Any], achievs: List[Any]) -> SchemaCreate:
        stats = GameParser.extract_stats(stats)
        achievs = GameParser.extract_achievs(achievs)

        return SchemaCreate(
            game_id=app_id,
            game_version=game_version,
            stats=stats,
            achievs=achievs
        )

    def _parse_achiev_data(self, app_id: int, raw_data: Dict[str, Any]) -> AchievDataAnalysisCreate:
        achievs = GameParser.extract_achievs_percent(raw_data)

        return AchievDataAnalysisCreate(
            game_id=app_id,
            achievs=achievs
        )

    def _parse_players_data(self, app_id: int, raw_data: Dict[str, Any]) -> PlayersDataAnalysisCreate:
        return PlayersDataAnalysisCreate(
            game_id=app_id,
            number_of_players=raw_data['player_count']
        )

    def _parse_reviews_data(self, app_id: int, raw_data: Dict[str, Any]) -> ReviewsDataAnalysisCreate:
        query_summary = raw_data['query_summary']
        reviews = GameParser.extract_reviews(raw_data)

        return ReviewsDataAnalysisCreate(
            game_id=app_id,
            num_reviews=query_summary['num_reviews'],
            review_score=query_summary['review_score'],
            review_score_desc=query_summary['review_score_desc'],
            total_positive=query_summary['total_positive'],
            total_negative=query_summary['total_negative'],
            total_reviews=query_summary['total_reviews'],
            reviews=reviews
        )

    def _parse_news_data(self, app_id: int, raw_data: Dict[str, Any]) -> NewsDataAnalysisCreate:
        news = GameParser.extract_news(raw_data)

        return NewsDataAnalysisCreate(
            game_id=app_id,
            news=news
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
