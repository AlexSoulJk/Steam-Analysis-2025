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
        pass

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