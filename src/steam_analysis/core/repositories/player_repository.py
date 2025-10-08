from .base import BaseRepository
from typing import List, Optional, Dict, Any

from ..codes.steamservices import SteamServices
from ...core.dependencies.basehttp import HTTPClient


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
