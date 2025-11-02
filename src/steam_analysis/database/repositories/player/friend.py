from typing import List, Optional, Dict, Tuple, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload

from ..base.base import BaseDBRepository
from ...models import Friend, User
from steam_analysis.core.schemas.player.player import FriendCreate, FriendResponse, FriendStatus


class FriendRepository(BaseDBRepository[Friend, FriendCreate, Any]):
    """Репозиторий для работы с дружескими связями"""

    def __init__(self):
        super().__init__(model=Friend)

    def get_friendship(self, session: Session, user_id: int, friend_id: int) -> Optional[Friend]:
        """Получить конкретную связь дружбы"""
        return session.query(Friend). \
            filter(
            Friend.user_id == user_id,
            Friend.friend_id == friend_id
        ).first()

    def get_friendship_bidirectional(self, session: Session, user_id: int, friend_id: int) -> Optional[Friend]:
        """Получить связь дружбы в любом направлении"""
        return session.query(Friend). \
            filter(
            or_(
                and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                and_(Friend.user_id == friend_id, Friend.friend_id == user_id)
            )
        ).first()

    def get_user_friends(self, session: Session, user_id: int,
                         status: Optional[FriendStatus] = None) -> List[Friend]:
        """Получить всех друзей пользователя"""
        query = session.query(Friend).filter(Friend.user_id == user_id)

        if status:
            query = query.filter(Friend.status == status.value)

        return query.all()

    def get_user_friends_with_details(self, session: Session, user_id: int,
                                      status: Optional[FriendStatus] = None) -> List[Friend]:
        """Получить друзей пользователя с информацией о друзьях"""
        query = session.query(Friend). \
            options(joinedload(Friend.friend)). \
            filter(Friend.user_id == user_id)

        if status:
            query = query.filter(Friend.status == status.value)

        return query.all()

    def create_friendship(self, session: Session, friend_create: FriendCreate) -> Friend:
        """Создать связь дружбы из схемы"""
        if friend_create.user_id == friend_create.friend_id:
            raise ValueError("Cannot add yourself as a friend")

        existing = self.get_friendship(session, friend_create.user_id, friend_create.friend_id)
        if existing:
            return existing

        # Просто передаем схему в модель - Pydantic автоматически обработает enum
        friend = Friend(**friend_create.model_dump())

        session.add(friend)
        session.commit()
        session.refresh(friend)
        return friend

    def get_existing_friendships(self, session: Session,
                                 friendships: List[Tuple[int, int]]) -> Dict[Tuple[int, int], Friend]:
        """
        Получить существующие связи дружбы (в обе стороны)
        Возвращает словарь {(user_id, friend_id): friend_object}
        """
        if not friendships:
            return {}

        conditions = []
        for user_id, friend_id in friendships:
            conditions.append(
                and_(Friend.user_id == user_id, Friend.friend_id == friend_id)
            )
            conditions.append(
                and_(Friend.user_id == friend_id, Friend.friend_id == user_id)
            )

        query = select(Friend).where(or_(*conditions))
        result = session.execute(query)
        existing_friends = result.scalars().all()

        friendship_map = {}
        for friend in existing_friends:
            friendship_map[(friend.user_id, friend.friend_id)] = friend
            friendship_map[(friend.friend_id, friend.user_id)] = friend

        return friendship_map

    def get_existing_user_ids(self, session: Session, user_ids: List[int]) -> set:
        """Получить множество существующих ID пользователей"""
        if not user_ids:
            return set()

        query = select(User.id).where(User.id.in_(user_ids))
        result = session.execute(query)
        return {row[0] for row in result}

    def create_friends_bulk(self, session: Session,
                            friends_create: List[FriendCreate]) -> Dict[str, Any]:
        """
        Массовое создание связей дружбы из схем
        """
        if not friends_create:
            return {
                'created': [],
                'updated': [],
                'skipped': [],
                'total_processed': 0,
                'total_created': 0,
                'total_updated': 0
            }

        # Подготавливаем данные для проверки
        friendship_pairs = [(fc.user_id, fc.friend_id) for fc in friends_create]
        existing_friendships = self.get_existing_friendships(session, friendship_pairs)

        # Получаем существующих пользователей
        all_user_ids = set()
        for fc in friends_create:
            all_user_ids.add(fc.user_id)
            all_user_ids.add(fc.friend_id)
        existing_user_ids = self.get_existing_user_ids(session, list(all_user_ids))

        created_friends = []
        updated_friends = []
        skipped_friends = []

        for friend_create in friends_create:
            user_id = friend_create.user_id
            friend_id = friend_create.friend_id

            # Проверяем, не пытаемся ли добавить себя в друзья
            if user_id == friend_id:
                skipped_friends.append(friend_create)
                continue

            # Определяем финальный статус на основе существования пользователей
            both_users_exist = user_id in existing_user_ids and friend_id in existing_user_ids
            final_status = FriendStatus.VALID if both_users_exist else FriendStatus.INVALID

            # Проверяем существование связи (в обе стороны)
            existing_key_forward = (user_id, friend_id)
            existing_key_reverse = (friend_id, user_id)

            existing_friend_forward = existing_friendships.get(existing_key_forward)
            existing_friend_reverse = existing_friendships.get(existing_key_reverse)

            if existing_friend_forward:
                # Связь уже существует в прямом направлении
                if existing_friend_forward.status != final_status.value:
                    existing_friend_forward.status = final_status.value
                    updated_friends.append(existing_friend_forward)
                else:
                    skipped_friends.append(friend_create)

            elif existing_friend_reverse:
                # Связь существует в обратном направлении - обновляем статус
                existing_friend_reverse.status = final_status.value
                updated_friends.append(existing_friend_reverse)

            else:
                # Создаем новую связь с финальным статусом используя model_dump()
                friend_data = friend_create.model_dump()
                friend_data['status'] = final_status.value  # Переопределяем статус

                new_friend = Friend(**friend_data)
                session.add(new_friend)
                created_friends.append(new_friend)

        session.commit()

        for friend in created_friends + updated_friends:
            session.refresh(friend)

        return {
            'created': created_friends,
            'updated': updated_friends,
            'skipped': skipped_friends,
            'total_processed': len(friends_create),
            'total_created': len(created_friends),
            'total_updated': len(updated_friends)
        }

    def update_friendship_status(self, session: Session, user_id: int,
                                 friend_id: int, status: FriendStatus) -> Optional[Friend]:
        """Обновить статус дружеской связи"""
        friendship = self.get_friendship(session, user_id, friend_id)
        if friendship:
            friendship.status = status.value
            session.commit()
            session.refresh(friendship)
        return friendship
