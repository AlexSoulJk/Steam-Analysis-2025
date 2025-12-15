from typing import List, Optional, Dict, Tuple, Any
from sqlalchemy import select, and_, or_, tuple_
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
        # session.commit()
        # session.refresh(friend)
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

    def get_existing_friendships_by_steamid(self, session: Session,
                                            steamid_pairs: List[Tuple[str, str]],
                                            batch_size: int = 900) -> Dict[Tuple[str, str], Friend]:
        """
        Получить существующие связи дружбы по парам steamid
        """
        if not steamid_pairs:
            return {}

        try:
            existing = []

            for i in range(0, len(steamid_pairs), batch_size):
                batch = steamid_pairs[i:i + batch_size]
                # WHERE (user_steamid, friend_steamid) IN ((id1, id2), (id3, id4), ...)
                query = session.query(Friend).filter(
                    tuple_(Friend.user_steamid, Friend.friend_steamid).in_(batch)
                )

                existing.extend(query.all())

            # batch_size = 800
            # for i in range(0, len(steamid_pairs), batch_size):
            #     batch = steamid_pairs[i:i + batch_size]
            #
            #     conditions = []
            #     for user_steamid, friend_steamid in batch:
            #         conditions.append(
            #             and_(
            #                 Friend.user_steamid == str(user_steamid),
            #                 Friend.friend_steamid == str(friend_steamid)
            #             )
            #         )
            #
            #     if conditions:
            #         batch_existing = session.query(Friend).filter(or_(*conditions)).all()
            #         existing.extend(batch_existing)

            # Создаем словарь для быстрого поиска

            result = {}
            for friendship in existing:
                key = (friendship.user_steamid, friendship.friend_steamid)
                result[key] = friendship

            return result

        except Exception as e:
            print(f"Error in get_existing_friendships_by_steamid: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def get_user_by_steamid(self, session: Session, steamid: str):
        return session.query(User).filter(User.steam_id == steamid).first()

    def get_existing_user_ids(self, session: Session, user_ids: List[str]) -> dict:
        """Получить множество существующих ID пользователей"""
        if not user_ids:
            return dict()

        query = select(User.id, User.steam_id).where(User.steam_id.in_(user_ids))
        result = session.execute(query)

        return {row.steam_id: row.id for row in result}

    def get_existing_friendship_ids(self, session: Session, user_ids: List[str], batch_size=900) -> dict:
        """Получить множество существующих ID пользователей"""
        if not user_ids:
            return dict()

        result = {}

        # Разбиваем на батчи
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]

            query = select(Friend).where(
                Friend.friend_steamid.in_(batch),
                Friend.status == FriendStatus.INVALID
            )

            batch_result = session.execute(query).scalars().all()

            # Группируем результаты
            for friendship in batch_result:
                if friendship.friend_steamid not in result:
                    result[friendship.friend_steamid] = []
                result[friendship.friend_steamid].append(friendship)

        return result
    # def create_friends_bulk(self, session: Session,
    #                         friends_create: List[FriendCreate]) -> Dict[str, Any]:
    #     """
    #     Массовое создание связей дружбы из схем
    #     """
    #     if not friends_create:
    #         return {
    #             'created': [],
    #             'updated': [],
    #             'skipped': [],
    #             'total_processed': 0,
    #             'total_created': 0,
    #             'total_updated': 0
    #         }
    #
    #     # Подготавливаем данные для проверки
    #     friendship_pairs = [(fc.user_id, fc.friend_id) for fc in friends_create]
    #     existing_friendships = self.get_existing_friendships(session, friendship_pairs)
    #
    #     # Получаем существующих пользователей
    #     all_user_ids = set()
    #     for fc in friends_create:
    #         all_user_ids.add(fc.user_id)
    #         all_user_ids.add(fc.friend_id)
    #     existing_user_ids = self.get_existing_user_ids(session, list(all_user_ids))
    #
    #     created_friends = []
    #     updated_friends = []
    #     skipped_friends = []
    #
    #     for friend_create in friends_create:
    #         user_id = friend_create.user_id
    #         friend_id = friend_create.friend_id
    #
    #         # Проверяем, не пытаемся ли добавить себя в друзья
    #         if user_id == friend_id:
    #             skipped_friends.append(friend_create)
    #             continue
    #
    #         # Определяем финальный статус на основе существования пользователей
    #         both_users_exist = user_id in existing_user_ids and friend_id in existing_user_ids
    #         final_status = FriendStatus.VALID if both_users_exist else FriendStatus.INVALID
    #
    #         # Проверяем существование связи (в обе стороны)
    #         existing_key_forward = (user_id, friend_id)
    #         existing_key_reverse = (friend_id, user_id)
    #
    #         existing_friend_forward = existing_friendships.get(existing_key_forward)
    #         existing_friend_reverse = existing_friendships.get(existing_key_reverse)
    #
    #         if existing_friend_forward:
    #             # Связь уже существует в прямом направлении
    #             if existing_friend_forward.status != final_status.value:
    #                 existing_friend_forward.status = final_status.value
    #                 updated_friends.append(existing_friend_forward)
    #             else:
    #                 skipped_friends.append(friend_create)
    #
    #         elif existing_friend_reverse:
    #             # Связь существует в обратном направлении - обновляем статус
    #             existing_friend_reverse.status = final_status.value
    #             updated_friends.append(existing_friend_reverse)
    #
    #         else:
    #             # Создаем новую связь с финальным статусом используя model_dump()
    #             friend_data = friend_create.model_dump()
    #             friend_data['status'] = final_status.value  # Переопределяем статус
    #
    #             new_friend = Friend(**friend_data)
    #             # session.add(new_friend)
    #             created_friends.append(new_friend)
    #
    #     session.add_all(created_friends)
    #     # session.commit()
    #     #
    #     # for friend in created_friends + updated_friends:
    #     #     session.refresh(friend)
    #
    #     return {
    #         'created': created_friends,
    #         'updated': updated_friends,
    #         'skipped': skipped_friends,
    #         'total_processed': len(friends_create),
    #         'total_created': len(created_friends),
    #         'total_updated': len(updated_friends)
    #     }

    def create_friends_bulk(self, session: Session,
                            friends_create: List[FriendCreate],
                            without_friends: List[User],
                            player_by_steam_id: Dict[str, User] = None,
                            friend_by_steam_id: Dict[str, User] = None) -> Dict[str, Any]:
        """
        Массовое создание связей дружбы из схем с учетом steamid в обе стороны
        """
        if not friends_create and not without_friends:
            return {
                'created': [],
                'updated': [],
                'skipped': [],
                'total_processed': 0,
                'total_created': 0,
                'total_updated': 0
            }

        # Собираем все steamid для проверки существующих связей
        steamid_pairs = []
        for fc in friends_create:
            steamid_pairs.append((fc.user_steamid, fc.friend_steamid))
            steamid_pairs.append((fc.friend_steamid, fc.user_steamid))

        # Получаем существующие связи по steamid парам
        existing_friendships_by_steamid = self.get_existing_friendships_by_steamid(
            session, steamid_pairs
        )

        # Получаем существующих пользователей
        all_steamids = set()
        all_user_steamids = set()
        dict_all_user_ids = {}
        for fc in friends_create:
            all_steamids.add(fc.friend_steamid)
            all_user_steamids.add(fc.user_steamid)
            if fc.user_steamid not in dict_all_user_ids:
                dict_all_user_ids[fc.user_steamid] = fc.user_id

        # existing_user_ids = self.get_existing_user_ids(session, list(all_steamids))

        created_friends = []
        updated_friends = []
        skipped_friends = []

        for friend_create in friends_create:
            user_id = friend_create.user_id
            friend_id = friend_create.friend_id
            user_steamid = friend_create.user_steamid
            friend_steamid = friend_create.friend_steamid

            # Проверяем, не пытаемся ли добавить себя в друзья
            if user_steamid == friend_steamid:
                skipped_friends.append(friend_create)
                continue

            # Если friend_id None, но оба пользователя существуют по steamid, статус VALID
            final_status = FriendStatus.VALID if (user_id and friend_id) else FriendStatus.INVALID

            # Проверяем существование связи по steamid парам (в обе стороны)
            steamid_key_forward = (user_steamid, friend_steamid)
            steamid_key_reverse = (friend_steamid, user_steamid)

            existing_friend_forward = existing_friendships_by_steamid.get(steamid_key_forward)
            existing_friend_reverse = existing_friendships_by_steamid.get(steamid_key_reverse)

            # НОВАЯ ЛОГИКА: Если friend_id None и статус INVALID, но связь существует
            if friend_id is None and final_status == FriendStatus.INVALID:
                if existing_friend_forward or existing_friend_reverse:
                    # Нашли существующую связь, нужно обновить friend_id и статус
                    existing_friend = existing_friend_forward or existing_friend_reverse

                    # Проверяем, можем ли мы получить friend_id по friend_steamid
                    # Для этого нужно найти пользователя с friend_steamid
                    friend_user = self.get_user_by_steamid(session, friend_steamid)
                    if friend_user:
                        # Обновляем существующую запись
                        existing_friend.friend_id = friend_user.id
                        existing_friend.status = FriendStatus.VALID.value
                        updated_friends.append(existing_friend)
                    else:
                        # Пользователь не найден, оставляем как есть
                        skipped_friends.append(friend_create)
                    continue

            # Старая логика обработки (с учетом steamid)
            if existing_friend_forward:
                # Связь уже существует в прямом направлении
                needs_update = False

                # Обновляем friend_id если он None
                if existing_friend_forward.friend_id is None and friend_id is not None:
                    existing_friend_forward.friend_id = friend_id
                    needs_update = True

                # Обновляем статус если изменился
                if existing_friend_forward.status != final_status.value:
                    existing_friend_forward.status = final_status.value
                    needs_update = True

                if needs_update:
                    updated_friends.append(existing_friend_forward)
                else:
                    skipped_friends.append(friend_create)

            elif existing_friend_reverse:
                # Связь существует в обратном направлении
                needs_update = False

                # В обратной связи роли меняются местами
                # user_id становится friend_id и наоборот
                # Здесь логика обновления зависит от бизнес-требований

                # Обновляем статус если изменился
                if existing_friend_reverse.status != final_status.value:
                    existing_friend_reverse.status = final_status.value
                    needs_update = True

                if existing_friend_reverse.friend_id is None and user_id is not None:
                    existing_friend_reverse.friend_id = user_id
                    needs_update = True

                if needs_update:
                    updated_friends.append(existing_friend_reverse)
                else:
                    skipped_friends.append(friend_create)

            else:
                # Создаем новую связь с финальным статусом используя model_dump()
                friend_data = friend_create.model_dump()
                friend_data['status'] = final_status.value  # Переопределяем статус

                new_friend = Friend(**friend_data)
                created_friends.append(new_friend)

        if created_friends:
            session.add_all(created_friends)
            session.flush()

        without_friends_steamids = [friend.steam_id for friend in without_friends]
        steam_ids = without_friends_steamids + list(all_user_steamids)

        existing_friends_for_with = self.get_existing_friendship_ids(session, steam_ids)
        if existing_friends_for_with:
            for user in without_friends:
                existing_friend = existing_friends_for_with.get(user.steam_id)
                if not existing_friend:
                    continue
                for friend in existing_friend:
                    friend.friend_id = user.id
                    friend.status = FriendStatus.VALID
                    updated_friends.append(friend)

            for fc in dict_all_user_ids:
                existing_friend = existing_friends_for_with.get(fc)
                if not existing_friend:
                    continue
                for friend in existing_friend:
                    friend.friend_id = dict_all_user_ids[fc]
                    friend.status = FriendStatus.VALID
                    updated_friends.append(friend)

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
            # session.commit()
            # session.refresh(friendship)
        return friendship
