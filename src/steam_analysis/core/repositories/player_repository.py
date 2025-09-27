from .base import BaseRepository
from typing import List, Optional, Dict, Any
from ...core.dependencies.basehttp import HTTPClient


class PlayerRepository(BaseRepository):
    def __init__(self, http_client: HTTPClient, api_key: str):
        self.http_client = http_client
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com"

    def get_by_id(self, steam_id: str) -> Optional[Dict[str, Any]]:
        """Получить игрока по SteamID"""
        url = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v2/"
        params = {'key': self.api_key, 'steamids': steam_id}

        data = self.http_client.get(url, params=params)
        players = data.get('response', {}).get('players', [])
        return players[0] if players else None

    def get_friends(self, steam_id: str) -> List[Dict[str, Any]]:
        """Получить друзей игрока"""
        url = f"{self.base_url}/ISteamUser/GetFriendList/v1/"
        params = {'key': self.api_key, 'steamid': steam_id, 'relationship': 'friend'}

        data = self.http_client.get(url, params=params)
        return data.get('friendslist', {}).get('friends', [])

    def get_owned_games(self, steam_id: str) -> List[Dict[str, Any]]:
        """Получить игры игрока"""
        url = f"{self.base_url}/IPlayerService/GetOwnedGames/v1/"
        params = {
            'key': self.api_key,
            'steamid': steam_id,
            'include_appinfo': 1,
            'include_played_free_games': 1
        }

        data = self.http_client.get(url, params=params)
        return data.get('response', {}).get('games', [])