# player_relations_creator.py
from typing import List, Dict
from sqlalchemy import and_
from sqlalchemy.orm import Session

from steam_analysis.database.models import (
    User, Friend, UserPlaytime, UserGameOwnership,
    UserAchievement, Review
)
from steam_analysis.core.schemas.player.player import FriendCreate, FriendStatus
from steam_analysis.core.schemas.player.playergame import OwnershipHttp, OwnershipCreate, \
    PlaytimeHttp, PlaytimeCreate, AchievementHttp, AchievementCreate, ReviewHttp, ReviewCreate
from steam_analysis.core.schemas.player.service import PlayerDataAnalysisCreate
from steam_analysis.database.support_models.player_creation import PreparedForPlayerCreation
from steam_analysis.database.repositories import (
    FriendRepository
)


class PlayerRelationsCreationService:

    def __init__(self):
        self.friend_repos = FriendRepository()

    def _prepare_relations(self, players: List[User],
                           dict_without_none: Dict[int, PlayerDataAnalysisCreate],
                           prep_info: PreparedForPlayerCreation):
        """Подготавливает все связи для создания"""

        friends = []
        # playtimes = []
        # ownerships = []
        # achievements = []
        # reviews = []

        for player in players:
            data = prep_info.friends[player.steam_id]

            # Подготовка друзей
            for friend_create in data:
                # Создаем уникальный ключ для проверки существования ???
                friends.append(FriendCreate(
                    user_id=player.id,
                    friend_id=friend_create.id
                ))

            # # Подготовка времени игры
            # for playtime_create in data.playtimes:
            #     playtime_key = f"{player.id}_{playtime_create.game_id}"
            #     if playtime_key not in prep_info.playtimes:
            #         playtimes.append(UserPlaytime(
            #             user_id=player.id,
            #             game_id=playtime_create.game_id,
            #             playtime_forever=playtime_create.playtime_forever,
            #             playtime_2weeks=playtime_create.playtime_2weeks,
            #             last_played=playtime_create.last_played
            #         ))
            #
            # # Подготовка владения играми
            # for ownership_create in data.owned_games:
            #     ownership_key = f"{player.id}_{ownership_create.game_id}"
            #     if ownership_key not in prep_info.ownerships:
            #         ownerships.append(UserGameOwnership(
            #             user_id=player.id,
            #             game_id=ownership_create.game_id,
            #             owned=ownership_create.owned
            #         ))
            #
            # # Подготовка достижений
            # for achievement_create in data.achievements:
            #     achievement_key = f"{player.id}_{achievement_create.game_id}_{achievement_create.achievement_id}"
            #     if achievement_key not in prep_info.achievements:
            #         achievements.append(UserAchievement(
            #             user_id=player.id,
            #             game_id=achievement_create.game_id,
            #             achievement_id=achievement_create.achievement_id,
            #             achieved=achievement_create.achieved,
            #             unlock_timestamp=achievement_create.unlock_timestamp,
            #             unlock_time=achievement_create.unlock_time
            #         ))
            #
            # # Подготовка отзывов
            # for review_create in data.reviews:
            #     if review_create.recommendation_id not in prep_info.reviews:
            #         reviews.append(Review(
            #             game_id=review_create.game_id,
            #             user_id=player.id,
            #             recommendation_id=review_create.recommendation_id,
            #             steam_id=review_create.steam_id,
            #             language=review_create.language,
            #             review=review_create.review,
            #             timestamp_created=review_create.timestamp_created,
            #             timestamp_updated=review_create.timestamp_updated,
            #             voted_up=review_create.voted_up,
            #             votes_up=review_create.votes_up,
            #             votes_funny=review_create.votes_funny,
            #             weighted_vote_score=review_create.weighted_vote_score,
            #             comment_count=review_create.comment_count,
            #             steam_purchase=review_create.steam_purchase,
            #             received_for_free=review_create.received_for_free,
            #             written_during_early_access=review_create.written_during_early_access,
            #             primarily_steam_deck=review_create.primarily_steam_deck
            #         ))

        return friends

    def create_connections_friends(self, prep_info: PreparedForPlayerCreation,
                                   players: List[User],
                                   session: Session):
        """Создает связи с друзьями для пользователей"""
        friends = []

        for player in players:
            data = prep_info.friends[player.steam_id]

            # Подготовка друзей
            for friend_create in data:
                friends.append(FriendCreate(
                    user_id=player.id,
                    user_steamid=player.steam_id,
                    friend_id=friend_create.id,
                    friend_steamid=friend_create.steam_id
                ))

            no_created_data = prep_info.no_created_friends.get(player.steam_id)
            for friend_data in no_created_data:
                friends.append(FriendCreate(
                    user_id=player.id,
                    user_steamid=player.steam_id,
                    friend_steamid=friend_data.steam_id,
                    status=FriendStatus.INVALID
                ))

        self.friend_repos.create_friends_bulk(session=session, friends_create=friends)

    def _filter_existing_relations(self, session, model, relations, unique_fields):
        """Фильтрует существующие связи массово - улучшенная версия"""
        if not relations:
            return []

        # Создаем списки значений для каждого поля
        field_values = {field: [] for field in unique_fields}
        for relation in relations:
            for field in unique_fields:
                field_values[field].append(getattr(relation, field))

        # Создаем условие с in_() для каждого поля
        conditions = []
        for field in unique_fields:
            if field_values[field]:
                conditions.append(getattr(model, field).in_(field_values[field]))

        if not conditions:
            return relations

        # Объединяем условия через AND (все поля должны совпадать)
        combined_condition = and_(*conditions)

        # Ищем существующие связи
        existing_relations = session.query(model).filter(combined_condition).all()
        existing_set = set(
            tuple(getattr(rel, field) for field in unique_fields)
            for rel in existing_relations
        )

        # Фильтруем только новые связи
        unique_relations = [
            relation for relation in relations
            if tuple(getattr(relation, field) for field in unique_fields) not in existing_set
        ]

        return unique_relations
