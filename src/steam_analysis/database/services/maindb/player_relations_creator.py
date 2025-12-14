# player_relations_creator.py
from typing import List, Dict, Tuple
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
    FriendRepository,
    PlayerRepository
)


class PlayerRelationsCreationService:

    def __init__(self):
        self.friend_repos = FriendRepository()
        self.player_repos = PlayerRepository()

    def _prepare_data_for_player_creation(self,
                                          data_without_none: List[PlayerDataAnalysisCreate],
                                          session: Session) -> Tuple[PreparedForPlayerCreation, List[str]]:
        """Подготовить данные для создания игроков"""
        friends_prep = {}
        no_created_friends_prep = {}
        no_created_friends = []
        friends_steam_ids = []
        for x in data_without_none:
            friends_steam_ids.extend(x.friends)
        existing_users = self.player_repos.get_existing_by_steam_ids(friends_steam_ids, session)

        for x in data_without_none:
            friends_prep[x.player.steam_id] = []
            no_created_friends_prep[x.player.steam_id] = []
            for friend_name in x.friends:
                # friend = self.player_repos.get_by_steam_id(friend_name, session)
                friend = existing_users.get(friend_name, None)
                if friend:
                    friends_prep[x.player.steam_id].append(friend)
                else:
                    no_created_friends_prep[x.player.steam_id].append(friend_name)
                    if friend_name not in no_created_friends:
                        no_created_friends.append(friend_name)

        return PreparedForPlayerCreation(friends=friends_prep, no_created_friends=no_created_friends_prep), \
            no_created_friends

    def create_connections_friends(self, data_without_none,
                                   players: List[User],
                                   session: Session):

        # Подготавливаем и создаем данные
        prep_info, no_created_friends = self._prepare_data_for_player_creation(
            data_without_none=data_without_none,
            session=session
        )

        """Создает связи с друзьями для пользователей"""
        friends = []
        friendships = []
        without_friends = []

        for player in players:
            data = prep_info.friends[player.steam_id]

            # Подготовка друзей
            for friend_create in data:
                if (player.steam_id, friend_create.steam_id) in friendships or \
                        (friend_create.steam_id, player.steam_id) in friendships:
                    continue

                friendships.append((player.steam_id, friend_create.steam_id))
                friendships.append((friend_create.steam_id, player.steam_id))

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
                    friend_steamid=friend_data,
                    status=FriendStatus.INVALID
                ))

            if not data and not no_created_data:
                without_friends.append(player)

        self.friend_repos.create_friends_bulk(session=session,
                                              friends_create=friends,
                                              without_friends=without_friends)

        return no_created_friends

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
