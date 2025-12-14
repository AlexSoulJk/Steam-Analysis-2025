from typing import Optional, List, Dict, Tuple, Any, Callable, Type
from sqlalchemy import select, and_, or_, over
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime

from steam_analysis.core.schemas.base import BaseSchema
from ..base.base import BaseDBRepository
from ...models import User, UserPlaytime, Friend, UserLogoffHistory, Game, UserGameOwnership
from steam_analysis.core.schemas.player.player import PlayerCreate, PlayerUpdate
from steam_analysis.core.schemas.player.playergame import LogoffHistoryCreate
from sqlalchemy import func, distinct





class PlayerRepository(BaseDBRepository[User, PlayerCreate, PlayerUpdate]):
    """Репозиторий для работы с пользователями/игроками"""

    def __init__(self):
        super().__init__(model=User)

    def get_by_steam_id(self, steam_id: str, session: Session) -> Optional[User]:
        """Получить пользователя по Steam ID"""
        return self.get_by_field("steam_id", steam_id, session=session)

    def get_country_game_stats(
            self,
            session: Session,
            *,
            with_geo: bool = True,
            min_count: int = 1,
            top_n: int = 3,
            count_expr_factory: Callable[[], Any],
            result_schema: Type[BaseSchema],
    ):
        """
        Получить топ-N игр по количеству пользователей в разрезе стран
        """

        count_expr = count_expr_factory().label("player_count")

        # === БАЗОВАЯ АГРЕГАЦИЯ: страна + игра ===
        base_query = (
            select(
                User.loccountrycode.label("country_code"),
                Game.name.label("game_name"),
                count_expr,
            )
            .select_from(User)
            .join(UserGameOwnership, UserGameOwnership.user_id == User.id)
            .join(Game, UserGameOwnership.game_id == Game.id)
        )

        # --- фильтр по гео ---
        geo_expr = func.coalesce(func.nullif(User.loccountrycode, ""), None)

        if with_geo:
            base_query = base_query.where(geo_expr.isnot(None))
        else:
            base_query = base_query.where(geo_expr.is_(None))

        base_subq = (
            base_query
            .group_by(User.loccountrycode, Game.id, Game.name)
            .having(count_expr >= min_count)
            .subquery()
        )

        # === RANKING (ROW_NUMBER) ===
        ranked_subq = (
            select(
                base_subq.c.country_code,
                base_subq.c.game_name,
                base_subq.c.player_count,
                func.row_number()
                .over(
                    partition_by=base_subq.c.country_code,
                    order_by=base_subq.c.player_count.desc()
                )
                .label("rank"),
            )
            .select_from(base_subq)
            .subquery()
        )

        # === ФИНАЛЬНЫЙ ЗАПРОС ===
        final_query = (
            select(
                ranked_subq.c.country_code,
                ranked_subq.c.game_name,
                ranked_subq.c.player_count,
            )
            .where(ranked_subq.c.rank <= top_n)
            .order_by(
                ranked_subq.c.country_code,
                ranked_subq.c.player_count.desc(),
            )
        )

        rows = session.execute(final_query).all()

        # === МАППИНГ В СХЕМУ ===
        return [
            result_schema(
                country_code=row.country_code,
                game_name=row.game_name,
                player_count=row.player_count,
            )
            for row in rows
        ]



    def get_existing_by_steam_ids(self, steam_ids: List[str], session: Session, batch_size=500) -> Dict[str, User]:
        """
        Получить существующих пользователей по списку steam_ids одним запросом
        Возвращает словарь {steam_id: user_object}
        """
        if not steam_ids:
            return {}

        query = select(self.model).where(self.model.steam_id.in_(steam_ids))
        result = session.execute(query)
        existing_users = result.scalars().all()
        result_dict = {}

        # Обрабатываем батчи
        for i in range(0, len(steam_ids), batch_size):
            batch = steam_ids[i:i + batch_size]
            query = select(self.model).where(self.model.steam_id.in_(batch))
            result = session.execute(query)
            existing_users = result.scalars().all()

            result_dict.update({user.steam_id: user for user in existing_users})
        return result_dict

    def create_bulk(self, objects_in: List[PlayerCreate], session: Session) -> List[User]:
        """
        Массовое создание пользователей

        Args:
            objects_in: Список Pydantic схем

        Returns:
            Список созданных пользователей
        """
        db_objects = []
        steam_ids = list(map(lambda x: x.steam_id, objects_in))
        existing_users_map = self.get_existing_by_steam_ids(steam_ids, session)

        new_users = [
            obj for obj in objects_in
            if obj.steam_id not in existing_users_map
        ]

        existing_users = list(existing_users_map.values())

        if not new_users:
            return existing_users

        for obj_in in new_users:
            obj_data = obj_in.model_dump(by_alias=True) if hasattr(obj_in, 'model_dump') else obj_in.dict()
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        session.add_all(db_objects)
        # session.commit()

        # for db_obj in db_objects:
        #     session.refresh(db_obj)

        return existing_users + db_objects

    def get_with_details(self, session: Session, user_id: int) -> Optional[User]:
        """Получить пользователя со всеми связанными данными"""
        return session.query(User). \
            options(
            joinedload(User.playtime).joinedload(UserPlaytime.game),
            joinedload(User.achievements),
            joinedload(User.reviews),
            joinedload(User.game_ownership),
            joinedload(User.logoff_history),
            joinedload(User.friends).joinedload(Friend.friend)
        ). \
            filter(User.id == user_id). \
            first()

    def get_by_steam_level(self, session: Session, min_level: int = 0, max_level: Optional[int] = None,
                           skip: int = 0, limit: int = 100) -> List[User]:
        """Получить пользователей по уровню Steam"""
        filters = {"steam_level": min_level}
        if max_level is not None:
            # Для диапазона используем кастомный фильтр
            query = session.query(User).filter(
                User.steam_level >= min_level,
                User.steam_level <= max_level
            )
            return query.offset(skip).limit(limit).all()

        return self.get_multi(skip=skip, limit=limit, filters=filters, session=session)

    def get_friends_list(self, session: Session, user_id: int,
                         status: str = 'valid') -> List[User]:
        """Получить список друзей пользователя"""
        return session.query(User). \
            join(Friend, Friend.friend_id == User.id). \
            filter(Friend.user_id == user_id, Friend.status == status). \
            all()

    def get_players_by_playtime_range(self, session: Session, game_id: int,
                                    min_minutes: int, max_minutes: int,
                                    skip: int = 0, limit: int = 100) -> List[User]:
        """Получить пользователей с временем игры в указанном диапазоне"""
        return session.query(User). \
            join(UserPlaytime). \
            filter(
            UserPlaytime.game_id == game_id,
            UserPlaytime.playtime_forever >= min_minutes,
            UserPlaytime.playtime_forever <= max_minutes
        ). \
            offset(skip).limit(limit).all()

    # === МЕТОДЫ ДЛЯ ИСТОРИИ ВЫХОДОВ ===
    def create_logoff_entry(self, session: Session,
                            user_id: int,
                            last_logoff: Optional[datetime] = None) -> UserLogoffHistory:
        """Создать запись о выходе пользователя"""
        if last_logoff is None:
            last_logoff = datetime.utcnow()

        logoff_entry = UserLogoffHistory(
            user_id=user_id,
            last_logoff=last_logoff
        )

        session.add(logoff_entry)
        # session.commit()
        # session.refresh(logoff_entry)
        return logoff_entry

    def create_logoff_entry_from_schema(self, session: Session,
                                        logoff_create: LogoffHistoryCreate) -> UserLogoffHistory:
        """Создать запись о выходе из схемы"""
        logoff_entry = UserLogoffHistory(**logoff_create.model_dump())
        session.add(logoff_entry)
        session.commit()
        session.refresh(logoff_entry)
        return logoff_entry

    def create_logoff_entries_bulk(self, session: Session,
                                   logoffs_data: List[LogoffHistoryCreate]) -> Dict[str, Any]:
        """Массовое создание записей о выходах"""
        if not logoffs_data:
            return {
                'created': [],
                'skipped': [],
                'total_processed': 0,
                'total_created': 0
            }

        logoff_entries = [
            UserLogoffHistory(**data.model_dump())
            for data in logoffs_data
        ]

        session.add_all(logoff_entries)
        # session.commit()
        #
        # for entry in logoff_entries:
        #     session.refresh(entry)

        return {
            'created': logoff_entries,
            'skipped': [],
            'total_processed': len(logoffs_data),
            'total_created': len(logoff_entries)
        }

    def get_last_logoff(self, session: Session, user_id: int) -> Optional[UserLogoffHistory]:
        """Получить последний выход пользователя"""
        return session.query(UserLogoffHistory). \
            filter(UserLogoffHistory.user_id == user_id). \
            order_by(UserLogoffHistory.last_logoff.desc()). \
            first()


    def update_user_last_logoff(self, session: Session, user_id: int,
                                last_logoff: Optional[datetime] = None) -> User:
        """Обновить last_logoff пользователя и создать запись в истории"""
        user = self.get(user_id, session=session)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        if last_logoff is None:
            last_logoff = datetime.utcnow()

        # Обновляем поле last_logoff у пользователя
        user.last_logoff = last_logoff

        # Создаем запись в истории
        self.create_logoff_entry(session, user_id, last_logoff)

        session.commit()
        session.refresh(user)
        return user

    def get_friends_by(self):
        pass
