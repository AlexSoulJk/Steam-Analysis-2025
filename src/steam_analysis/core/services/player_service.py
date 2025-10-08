from typing import List, Dict, Any, Optional
from ..repositories.player_repository import PlayerRepository
from ..repositories.game_repository import GameRepository


class PlayerService:
    def __init__(self, player_repo: PlayerRepository, game_repo: GameRepository):
        self.player_repo = player_repo
        self.game_repo = game_repo

    def get_player_profile(self, steam_id: str) -> Optional[Dict[str, Any]]:
        """Получить полный профиль игрока"""
        profile = self.player_repo.get_by_id(steam_id)
        if not profile:
            return None

        # Обогащаем данными
        games = self.player_repo.get_owned_games(steam_id)
        friends = self.player_repo.get_friends(steam_id)
        steam_level = self.player_repo.get_steam_level(steam_id)

        return {
            'profile': profile,
            'steam_level': steam_level,
            'games_count': len(games),
            'games_ids': [game.get('appid') for game in games],
            'friends_count': len(friends),
            'friends_ids': [friend.get('steamid') for friend in friends],
            'total_playtime': sum(game.get('playtime_forever', 0) for game in games),
            'recent_games': sorted(games, key=lambda x: x.get('playtime_forever', 0), reverse=True)[:5]
        }

    def analyze_gaming_preferences(self, steam_id: str) -> Dict[str, Any]:
        """Проанализировать игровые предпочтения"""
        games = self.player_repo.get_owned_games(steam_id)

        # Анализ жанров, времени и т.д.
        total_playtime = sum(game.get('playtime_forever', 0) for game in games)
        avg_playtime = total_playtime / len(games) if games else 0

        return {
            'total_games': len(games),
            'total_playtime_minutes': total_playtime,
            'total_playtime_hours': total_playtime // 60,
            'average_playtime_per_game': avg_playtime,
            'most_played': max(games, key=lambda x: x.get('playtime_forever', 0)) if games else None
        }
