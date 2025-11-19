from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from steam_analysis.core.schemas.player.service import PlayerDataAnalysisCreate
from steam_analysis.core.services.schema_morpher import SchemaMorpher
from steam_analysis.database.models import User
from steam_analysis.database.repositories import (
    PlayerRepository,
    PlayerPlaytimeRepository,
    PlayerGameOwnershipRepository,
    PlayerAchievementRepository,
    FriendRepository,
    ReviewRepository
)
from steam_analysis.database.support_models.player_creation import PreparedForPlayerCreation


class PlayerCreationService:
    """Сервис для создания игроков и связанных данных"""

    def __init__(self):
        self.player_repos = PlayerRepository()
        self.playtime_repos = PlayerPlaytimeRepository()
        self.ownership_repos = PlayerGameOwnershipRepository()
        self.achievement_repos = PlayerAchievementRepository()
        self.friend_repos = FriendRepository()
        self.review_repos = ReviewRepository()

    def _prepare_data_for_player_creation(self,
                                          data_without_none: List[PlayerDataAnalysisCreate],
                                          session: Session) -> PreparedForPlayerCreation:
        """Подготовить данные для создания игроков"""
        # Создаем игроков
        playtimes = list(map(lambda x: x.playtimes, data_without_none))
        ownerships = list(map(lambda x: x.owned_games, data_without_none))
        friends = list(map(lambda x: x.friends, data_without_none))
        achievements = list(map(lambda x: x.achievements, data_without_none))
        reviews = list(map(lambda x: x.reviews, data_without_none))

        # Подготавливаем связанные данные
        playtimes = self.playtime_repos.create_playtimes_bulk(session=session, playtimes_data=playtimes)
        ownerships = self.ownership_repos.create_ownerships_bulk(session=session, ownerships_data=ownerships)
        friends = self.friend_repos.create_friends_bulk(session=session, friends_create=friends)

        # Для достижений и отзывов потребуются дополнительные данные о играх
        achievements = self.achievement_repos.create_achievements_bulk(session=session, achievements_data=achievements)
        reviews = self.review_repos.create_reviews_bulk(session=session, reviews_data=reviews)

        return PreparedForPlayerCreation(
            playtimes=playtimes.get('created', []) + playtimes.get('updated', []),
            ownerships=ownerships.get('created', []) + ownerships.get('updated', []),
            achievements=achievements.get('created', []) + achievements.get('updated', []),
            friends=friends.get('created', []) + friends.get('updated', []),
            reviews=reviews.get('created', []) + reviews.get('updated', []),
        )

    def create_chunk_players(self,
                             players_info_chunk: List[Optional[PlayerDataAnalysisCreate]],
                             session: Session) -> Tuple[
        List[User], PreparedForPlayerCreation, Dict[str, PlayerDataAnalysisCreate]]:
        """Создать чанк игроков с связанными данными"""

        # Фильтруем None значения
        data_without_none = list(filter(lambda x: x is not None, players_info_chunk))
        dict_without_none = {data_analysis_schema.player.steam_id: data_analysis_schema
                             for data_analysis_schema in data_without_none}

        # Подготавливаем и создаем данные
        prep_info = self._prepare_data_for_player_creation(
            data_without_none=data_without_none,
            session=session
        )

        player_to_create = SchemaMorpher.user_create_from_http_to_database(
            players=list(map(lambda x: x.player, data_without_none)))

        players = self.player_repos.create_bulk(player_to_create, session=session)

        return players, prep_info, dict_without_none
