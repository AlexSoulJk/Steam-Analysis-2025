import datetime
from typing import List, Dict, Any, Optional, Set
from ..repositories.player_repository import PlayerRepository
from ..repositories.game_repository import GameRepository
from ..schemas.analysis.game import GameAnalysisChunkForResponse
from ..schemas.analysis.user import UserAnalysisChunkForResponse
from ..schemas.player.service import FillPlayerAnalysisChunk, PlayerDataAnalysisCreate, FillPlayerSchemaChunk,\
    PlayerAnalysesSchema
from ..schemas.player.player import PlayerFromHttp, PlayerFullFromHttp
from ..schemas.player.playergame import AchievementBase, OwnershipBase, ReviewBase, PlaytimeBase


class PlayerService:
    def __init__(self, player_repo: PlayerRepository, game_repo: GameRepository):
        self.player_repo = player_repo
        self.game_repo = game_repo

    def get_players_ids_by_one(self, steam_id: str, depth: int = 1) -> List[str]:
        """
        Рекурсивно находит Steam ID друзей до указанной глубины
        """
        if depth <= 0:
            return []

        visited: Set[str] = set()
        self._collect_friends_recursive(steam_id, depth, visited)

        visited.discard(steam_id)
        return list(visited)

    def _collect_friends_recursive(self, current_id: str, depth: int, visited: Set[str]):
        if current_id in visited:
            return

        visited.add(current_id)

        if depth <= 0:
            return

        try:
            friends = self.player_repo.get_friends(current_id)
            friend_ids = [friend.get('steamid') for friend in friends if friend.get('steamid')]

            for friend_id in friend_ids:
                self._collect_friends_recursive(friend_id, depth - 1, visited)

        except Exception as e:
            print(f"Error getting friends for {current_id}: {e}")

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

    def get_player_data_analysis(self, chunk_procession: UserAnalysisChunkForResponse) -> FillPlayerAnalysisChunk:
        start_time = datetime.datetime.now()

        if not steam_ids:
            response_time = datetime.datetime.now() - start_time

            return FillPlayerAnalysisChunk(
                start_steam_id="",
                end_steam_id="",
                response_time=response_time,
                data_chunk=[],
                processed_count=0,
                success_count=0,
                error_count=0
            )

        # Сортируем Steam ID для определения диапазона
        sorted_steam_ids = sorted(steam_ids)
        start_steam_id = sorted_steam_ids[0]
        end_steam_id = sorted_steam_ids[-1]

        players_data = self.player_repo.get_by_ids(steam_ids)
        data_chunk = self._create_data_chunk_from_players(sorted_steam_ids, players_data)

        # Рассчитываем время выполнения
        response_time = datetime.datetime.now() - start_time

        # Создаем чанк
        chunk = FillPlayerAnalysisChunk(
            start_steam_id=start_steam_id,
            end_steam_id=end_steam_id,
            response_time=response_time,
            data_chunk=data_chunk
        )

        # Автоматически рассчитываем статистику
        chunk.calculate_stats()

        return chunk

    def _create_data_chunk_from_players(
            self,
            sorted_steam_ids: List[str],
            players_data: List[Dict[str, Any]]
    ) -> List[Optional[PlayerDataAnalysisCreate]]:

        if not players_data:
            return [None] * len(sorted_steam_ids)

        # Создаем словарь для быстрого доступа по steam_id
        players_dict = {player['steamid']: player for player in players_data}
        data_chunk = []

        for steam_id in sorted_steam_ids:
            if steam_id in players_dict:
                player_from_http = self._create_player_from_Http(players_dict[steam_id])
                player_analysis = PlayerDataAnalysisCreate(player=player_from_http)
                data_chunk.append(player_analysis)
            else:
                data_chunk.append(None)

        return data_chunk

    def _create_player_from_Http(self, player_data: Dict[str, Any]) -> Optional[PlayerFromHttp]:
        """Создать объект игрока из Http"""
        try:
            # Безопасное извлечение timestamp полей
            time_created = None
            if 'timecreated' in player_data and player_data['timecreated']:
                time_created = datetime.datetime.fromtimestamp(player_data['timecreated'])

            last_logoff = None
            if 'lastlogoff' in player_data and player_data['lastlogoff']:
                last_logoff = datetime.datetime.fromtimestamp(player_data['lastlogoff'])

            steam_id = player_data.get('steamid', '')
            # friends = self.player_repo.get_friends(steam_id)
            steam_level = self.player_repo.get_steam_level(steam_id)

            return PlayerFromHttp(
                steam_id=player_data.get('steamid', ''),
                persona_name=player_data.get('personaname'),
                profile_url=player_data.get('profileurl'),
                avatar_url=player_data.get('avatar'),
                avatar_medium_url=player_data.get('avatarmedium'),
                avatar_full_url=player_data.get('avatarfull'),
                time_created=time_created,
                profile_state=player_data.get('profilestate'),
                community_visibility_state=player_data.get('communityvisibilitystate'),
                last_logoff=last_logoff,
                # friends=[friend['steamid'] for friend in friends] if friends else [],
                steam_level=steam_level,
                loccountrycode=player_data.get('loccountrycode'),
                locstatecode=player_data.get('locstatecode'),
                loccityid=player_data.get('loccityid')
            )
        except Exception as e:
            print(f"Error creating player base: {e}")
            return None

    def get_player_game_data(self, steam_ids: list[str]) -> FillPlayerSchemaChunk:
        """Получить данные по играм для пользователей"""
        start_time = datetime.datetime.now()

        if not steam_ids:
            response_time = datetime.datetime.now() - start_time
            return FillPlayerSchemaChunk(
                steam_ids=[],
                start_time=start_time,
                data_chunk={},
                response_time=response_time,
                success_count=0
            )

        # Сортируем Steam ID для консистентности
        sorted_steam_ids = sorted(steam_ids)
        data_chunk = {}
        success_count = 0

        # Обрабатываем каждого игрока
        for steam_id in sorted_steam_ids:
            try:
                print(f"Start processed {steam_id}")
                owned_games = self._get_structured_owned_games(steam_id)

                player_analysis = PlayerAnalysesSchema(
                    owned_games=owned_games
                )
                data_chunk[steam_id] = player_analysis
                success_count += 1
                print(f"Successfully processed {steam_id}")

            except Exception as e:
                print(f"Error processing {steam_id}: {e}")
                continue

        response_time = datetime.datetime.now() - start_time

        return FillPlayerSchemaChunk(
            steam_ids=sorted_steam_ids,
            start_time=start_time,
            data_chunk=data_chunk,
            response_time=response_time,
            success_count=success_count
        )

    def _get_structured_owned_games(self, steam_id: str) -> Dict[str, Dict[str, Any]]:
        """Получить структурированные данные об играх"""
        try:
            owned_games_data = self.player_repo.get_owned_games(steam_id)
            structured_games = {}

            for game in owned_games_data:
                app_id = str(game.get('appid'))

                # Создаем OwnershipBase
                # ownership = OwnershipBase(
                #     owned=True
                # )

                # Создаем PlaytimeBase
                last_played = None
                if game.get('last_played'):
                    last_played = datetime.datetime.fromtimestamp(game['last_played'])

                playtime = PlaytimeBase(
                    user_id=0,
                    game_id=0,
                    playtime_forever=game.get('playtime_forever', 0),
                    playtime_2weeks=game.get('playtime_2weeks', 0),
                    last_played=last_played
                )

                # Получаем достижения для этой игры
                achievements = self.player_repo.get_player_achievements(steam_id, app_id)

                # Получаем заработанные статистики
                stats = self.player_repo.get_player_game_stats(steam_id, app_id)

                # Структурируем данные
                structured_games[app_id] = {
                    # 'owned': ownership,
                    'playtime': playtime,
                    'achievements': achievements,
                    'stats': stats
                }

            return structured_games

        except Exception as e:
            print(f"Error getting structured games for {steam_id}: {e}")
            return {}
