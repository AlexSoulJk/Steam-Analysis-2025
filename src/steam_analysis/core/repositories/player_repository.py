from .base import BaseRepository
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from ..schemas.analysis.user import UserAnalysisChunkForResponse, UserAnalysisChunkForRequest, \
    UserAnalysisUpdate, UserAnalysisResponse

from ..schemas.player.service import PlayerGameDataAnalysisCreate, PlayerDataAnalysisCreate, FillPlayerSchemaChunk,\
    PlayerAnalysesSchema
from ..schemas.player.player import PlayerFromHttp, PlayerFullFromHttp
from ..schemas.player.playergame import AchievementHttp, OwnershipHttp, PlaytimeHttp

from ..codes.steamservices import SteamServices
from ...core.dependencies.basehttp import HTTPClient

import logging

logger = logging.getLogger(__name__)


class PlayerRepository(BaseRepository):
    API_STEAM_POWERED_URL = "https://api.steampowered.com"

    def __init__(self, http_client: HTTPClient, api_key: str):
        self.http_client = http_client
        self.api_key = api_key

    def get_by_id(self, steam_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Получить игрока по SteamID"""
        url = f"{PlayerRepository.API_STEAM_POWERED_URL}/{SteamServices.ISteamUser}/GetPlayerSummaries/v2/"
        params = {'key': self.api_key, 'steamids': steam_id}
        data = self.http_client.get(url, params=params)
        players = data.get('response', {}).get('players', [])
        return players[0] if players else None

    def get_by_ids(self, steam_ids: list[str], **kwargs) -> Optional[List[Any]]:
        """Получить информацию по списку SteamID игроков"""
        butch_size = 30
        all_amount = len(steam_ids)
        len_butches = all_amount // butch_size
        players = []
        print(all_amount, len_butches)
        for index in range(len_butches):
            part_ids = steam_ids[index*butch_size:butch_size*(index + 1)]
            url = f"{PlayerRepository.API_STEAM_POWERED_URL}/{SteamServices.ISteamUser}/GetPlayerSummaries/v2/"
            params = {'key': self.api_key, 'steamids': ','.join(part_ids)}
            data = self.http_client.get(url, params=params)
            part_players = data.get('response', {}).get('players', [])
            players.extend(part_players)

        return players if players else None

    def get_by_list_ids(self, steam_ids: list[str]) -> Optional[List[Any]]:
        """Получить информацию по списку SteamID игроков"""
        url = f"{PlayerRepository.API_STEAM_POWERED_URL}/{SteamServices.ISteamUser}/GetPlayerSummaries/v2/"
        params = {'key': self.api_key, 'steamids': ','.join(steam_ids)}
        data = self.http_client.get(url, params=params)
        players = data.get('response', {}).get('players', [])

        return players if players else None

    def get_friends(self, steam_id: str) -> List[Dict[str, Any]]:
        """Получить друзей игрока"""
        url = f"{PlayerRepository.API_STEAM_POWERED_URL}/{SteamServices.ISteamUser}/GetFriendList/v1/"
        params = {'key': self.api_key, 'steamid': steam_id, 'relationship': 'friend'}
        data = self.http_client.get(url, params=params)
        return data.get('friendslist', {}).get('friends', [])

    def get_owned_games(self, steam_id: str) -> List[Dict[str, Any]]:
        """Получить игры игрока"""
        url = f"{PlayerRepository.API_STEAM_POWERED_URL}/{SteamServices.IPlayerService}/GetOwnedGames/v1/"
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'include_appinfo': 1,
            'include_played_free_games': 1
        }

        data = self.http_client.get(url, params=params)
        return data.get('response', {}).get('games', [])

    def get_steam_level(self, steam_id: str) -> int:
        """Получить уровень игрока"""
        url = f"{PlayerRepository.API_STEAM_POWERED_URL}/{SteamServices.IPlayerService}/GetSteamLevel/v1/"
        params = {
            'key': self.api_key,
            'steamid': steam_id,
        }

        data = self.http_client.get(url, params=params)
        return data.get('response', {}).get('player_level')

    def get_player_achievements(self, steam_id: str, app_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получить достижения игрока по его SteamId и app_id игры"""
        url = f"{PlayerRepository.API_STEAM_POWERED_URL}/{SteamServices.ISteamUserStats}/GetPlayerAchievements/v1/"
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'appid': app_id,
        }
        try:
            data = self.http_client.get(url, params=params)
            return data.get('playerstats', {}).get('achievements', [])
        except:
            return None

    def get_player_game_stats(self, steam_id: str, app_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получить статистики игрока по его SteamId в игры с app_id """
        url = f"{PlayerRepository.API_STEAM_POWERED_URL}/{SteamServices.ISteamUserStats}/GetUserStatsForGame/v2/"
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'appid': app_id,
        }
        try:
            data = self.http_client.get(url, params=params)
            return data.get('playerstats', {}).get('stats', [])
        except:
            return None

    def get_player_data(self, user_for_response: UserAnalysisResponse) -> \
            Tuple[Optional[PlayerDataAnalysisCreate], UserAnalysisUpdate]:
        """
        Получение данных пользователя по схеме (аналог get_by_schema для игр)
        """
        steam_id = str(user_for_response.steam_id)
        error_log_message = ""
        status = ""
        request_model = None

        try:
            # Получаем основные данные профиля
            profile_data = self.get_by_id(steam_id)

            if not profile_data:
                error_log_message = f"Player steam_id: {steam_id} not found or failed to load"
                status = "null_state"
                logger.warning(f"\n ❗️ {error_log_message}")
            else:
                status = "particle"
                # Получаем дополнительные данные (друзья, игры и т.д.)
                request_model = self._parse_player_data(steam_id, profile_data)

        except Exception as e:
            status = "failed"
            error_log_message = f"Error getting player: {e}"
            logger.error(f"\n ❗❗️ {error_log_message}")

        return request_model, UserAnalysisUpdate.from_response_schema(
            response=user_for_response,
            status=status,
            error_log=error_log_message
        )

    def get_players_data_batch(self, users_for_response: List[UserAnalysisResponse]) -> List[
        Tuple[Optional[PlayerDataAnalysisCreate], UserAnalysisUpdate]]:
        """
        Массовое получение данных пользователей по схеме с использованием get_by_ids
        """
        start_time = datetime.now()
        results = []

        if not users_for_response:
            return []

        try:
            # Собираем все steam_id для массового запроса
            steam_ids = [str(user.steam_id) for user in users_for_response]

            # Массово получаем данные профилей
            profiles_data = self.get_by_list_ids(steam_ids) or []

            # Создаем словарь для быстрого доступа к данным по steam_id
            profiles_dict = {profile['steamid']: profile for profile in profiles_data}

            # Обрабатываем каждого пользователя
            for user_response in users_for_response:
                steam_id = str(user_response.steam_id)
                error_log_message = ""
                status = ""
                request_model = None

                try:
                    profile_data = profiles_dict.get(steam_id)

                    if not profile_data:
                        error_log_message = f"Player steam_id: {steam_id} not found or failed to load"
                        status = "null_state"
                        logger.warning(f"\n ❗️ {error_log_message}")
                    else:
                        status = "particle"
                        # Получаем дополнительные данные (друзья, игры и т.д.)
                        request_model = self._parse_player_data(steam_id, profile_data)

                except Exception as e:
                    status = "failed"
                    error_log_message = f"Error getting player {steam_id}: {e}"
                    logger.error(f"\n ❗❗️ {error_log_message}")

                user_update = UserAnalysisUpdate.from_response_schema(
                    response=user_response,
                    status=status,
                    error_log=error_log_message
                )

                results.append((request_model, user_update))

        except Exception as e:
            # Обработка ошибок на уровне всего батча
            logger.error(f"Error in batch players data processing: {e}")
            # Возвращаем ошибки для всех пользователей в случае сбоя батча
            for user_response in users_for_response:
                error_update = UserAnalysisUpdate.from_response_schema(
                    response=user_response,
                    status="failed",
                    error_log=f"Batch processing error: {e}"
                )
                results.append((None, error_update))

        response_time = datetime.now() - start_time
        logger.info(f"Processed {len(users_for_response)} players in {response_time.total_seconds()} seconds")

        return results

    def _parse_player_data(self, steam_id: str, raw_data: Dict[str, Any]) -> PlayerDataAnalysisCreate:
        """
        Парсинг сырых данных игрока в структурированный формат для анализа
        (аналог _parse_game_data)
        """
        # Основная информация об игроке
        player_base = self._create_player_base(raw_data)

        # Получаем информацию о друзьях
        friends_data = self._get_friends_data(steam_id)

        return PlayerDataAnalysisCreate(
            player=player_base,
            friends=friends_data
        )

    def _create_player_base(self, raw_data: Dict[str, Any]) -> PlayerFromHttp:
        """
        Создание базового объекта игрока из сырых данных
        """
        # Обработка timestamp полей
        time_created = None
        if 'timecreated' in raw_data and raw_data['timecreated']:
            time_created = datetime.fromtimestamp(raw_data['timecreated'])

        last_logoff = None
        if 'lastlogoff' in raw_data and raw_data['lastlogoff']:
            last_logoff = datetime.fromtimestamp(raw_data['lastlogoff'])

        # Получаем уровень Steam
        steam_level = self.get_steam_level(raw_data.get('steamid', ''))

        return PlayerFromHttp(
            steam_id=raw_data.get('steamid', ''),
            persona_name=raw_data.get('personaname'),
            profile_url=raw_data.get('profileurl'),
            avatar_url=raw_data.get('avatar'),
            avatar_medium_url=raw_data.get('avatarmedium'),
            avatar_full_url=raw_data.get('avatarfull'),
            time_created=time_created,
            community_visibility_state=raw_data.get('communityvisibilitystate'),
            last_logoff=last_logoff,
            steam_level=steam_level,
            loccountrycode=raw_data.get('loccountrycode'),
            locstatecode=raw_data.get('locstatecode'),
            loccityid=raw_data.get('loccityid')
        )

    def _get_friends_data(self, steam_id: str) -> List[str]:
        """
        Получение и парсинг данных о друзьях
        """
        try:
            friends_raw = self.get_friends(steam_id)
            if not friends_raw:
                return []

            return [friend.get('steamid') for friend in friends_raw if friend.get('steamid')]

        except Exception as e:
            logger.error(f"Error getting friends data for {steam_id}: {e}")
            return []

    def get_player_game_data(self, user_for_response: UserAnalysisResponse) -> \
            Tuple[Optional[PlayerGameDataAnalysisCreate], UserAnalysisUpdate]:
        """
        Получение данных пользователя по схеме (аналог get_by_schema для игр)
        """
        steam_id = str(user_for_response.steam_id)
        error_log_message = ""
        status = ""
        request_model = None

        try:
            if not steam_id:
                error_log_message = f"Player steam_id: {steam_id} not found or failed to load"
                status = "null_state"
                logger.warning(f"\n ❗️ {error_log_message}")
            else:
                status = "particle"  #или другой статус??
                # Получаем дополнительные данные по играм пользователя
                request_model = self._parse_player_game_data(steam_id)

        except Exception as e:
            status = "failed"
            error_log_message = f"Error getting player: {e}"
            logger.error(f"\n ❗❗️ {error_log_message}")

        return request_model, UserAnalysisUpdate.from_response_schema(
            response=user_for_response,
            status=status,
            error_log=error_log_message
        )

    def _parse_player_game_data(self, steam_id: str) -> \
            Optional[PlayerGameDataAnalysisCreate]:
        """
        Парсинг данных игрока и преобразование в схему PlayerGameDataAnalysisCreate
        с обработкой ошибок
        """
        try:
            owned_games = []
            playtimes = []
            achievements = []

            # Получаем список игр пользователя
            games_data = self.get_owned_games(steam_id)

            if not games_data:
                logger.warning(f"No games found for user {steam_id}")
                return None

            for game in games_data:
                app_id = str(game.get('appid', ''))

                # Создаем запись о владении игрой
                ownership = OwnershipHttp(
                    steam_id=steam_id,
                    app_id=app_id
                )
                owned_games.append(ownership)

                # Создаем запись о времени игры
                playtime = PlaytimeHttp(
                    steam_id=steam_id,
                    app_id=app_id,
                    playtime_forever=game.get('playtime_forever'),
                    playtime_2weeks=game.get('playtime_2weeks'),
                    last_played=self._convert_timestamp_to_datetime(game.get('rtime_last_played'))
                )
                playtimes.append(playtime)

                # Получаем достижения для игры (может быть None если недоступны)
                game_achievements = self.get_player_achievements(steam_id, app_id)
                if game_achievements:
                    for ach in game_achievements:
                        if ach.get('achieved', 0) == 1:
                            achievement = AchievementHttp(
                                steam_id=steam_id,
                                app_id=app_id,
                                apiname=ach.get('apiname', ''),
                                achieved=True,
                                unlock_timestamp=ach.get('unlocktime'),
                                unlock_time=self._convert_timestamp_to_datetime(ach.get('unlocktime'))
                            )
                            achievements.append(achievement)

            return PlayerGameDataAnalysisCreate(
                owned_games=owned_games,
                playtimes=playtimes,
                achievements=achievements
            )

        except Exception as e:
            logger.error(f"Error parsing player data for {steam_id}: {e}")
            return None

    def _convert_timestamp_to_datetime(self, timestamp: Optional[int]) -> Optional[datetime]:
        """
        Конвертирует Unix timestamp в datetime объект
        """
        if timestamp and timestamp > 0:
            return datetime.fromtimestamp(timestamp)
        return None
