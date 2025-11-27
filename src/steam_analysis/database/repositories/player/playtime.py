from typing import Optional, List, Dict, Tuple, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime

from ..base.base import BaseDBRepository
from ...models import UserPlaytime
from steam_analysis.core.schemas.player.playergame import PlaytimeCreate


class PlayerPlaytimeRepository(BaseDBRepository[UserPlaytime, PlaytimeCreate, Any]):
    """Репозиторий для работы с временем игры пользователей"""

    def __init__(self):
        super().__init__(model=UserPlaytime)

    def get_user_playtime(self, session: Session, user_id: int, game_id: int) -> Optional[UserPlaytime]:
        """Получить время игры пользователя для конкретной игры"""
        return session.query(UserPlaytime). \
            filter(
            UserPlaytime.user_id == user_id,
            UserPlaytime.game_id == game_id
        ).first()

    def get_user_playtimes(self, session: Session, user_id: int,
                           skip: int = 0, limit: int = 100) -> List[UserPlaytime]:
        """Получить все время игры пользователя"""
        return session.query(UserPlaytime). \
            filter(UserPlaytime.user_id == user_id). \
            offset(skip).limit(limit).all()

    def get_existing_playtimes(self, session: Session,
                               playtime_pairs: List[Tuple[int, int]]) -> Dict[Tuple[int, int], UserPlaytime]:
        """
        Получить существующие записи времени игры
        Возвращает словарь {(user_id, game_id): playtime_object}
        """
        if not playtime_pairs:
            return {}

        conditions = []
        for user_id, game_id in playtime_pairs:
            conditions.append(
                and_(UserPlaytime.user_id == user_id, UserPlaytime.game_id == game_id)
            )

        query = select(UserPlaytime).where(or_(*conditions))
        result = session.execute(query)
        existing_playtimes = result.scalars().all()

        return {(pt.user_id, pt.game_id): pt for pt in existing_playtimes}

    def create_or_update_playtime(self, session: Session,
                                  playtime_create: PlaytimeCreate) -> UserPlaytime:
        """Создать или обновить время игры"""
        existing = self.get_user_playtime(
            session,
            playtime_create.user_id,
            playtime_create.game_id
        )

        if existing:
            # Обновляем существующую запись
            for key, value in playtime_create.model_dump().items():
                if value is not None:
                    setattr(existing, key, value)
        else:
            # Создаем новую запись
            existing = UserPlaytime(**playtime_create.model_dump())
            session.add(existing)

        # session.commit()
        # session.refresh(existing)
        return existing

    def create_playtimes_bulk(self, session: Session,
                              playtimes_data: List[PlaytimeCreate]) -> Dict[str, Any]:
        """Массовое создание/обновление времени игры"""
        if not playtimes_data:
            return {
                'created': [],
                'updated': [],
                'skipped': [],
                'total_processed': 0,
                'total_created': 0,
                'total_updated': 0
            }

        # Собираем все пары (user_id, game_id) для проверки
        playtime_pairs = [(pt.user_id, pt.game_id) for pt in playtimes_data]

        # Получаем существующие записи за один запрос
        existing_playtimes = self.get_existing_playtimes(session, playtime_pairs)

        created_playtimes = []
        updated_playtimes = []
        skipped_playtimes = []

        for playtime_data in playtimes_data:
            user_id = playtime_data.user_id
            game_id = playtime_data.game_id

            existing_playtime = existing_playtimes.get((user_id, game_id))

            if existing_playtime:
                # Обновляем существующую запись
                updated = False
                for key, value in playtime_data.model_dump().items():
                    if value is not None and getattr(existing_playtime, key) != value:
                        setattr(existing_playtime, key, value)
                        updated = True

                if updated:
                    updated_playtimes.append(existing_playtime)
                else:
                    skipped_playtimes.append(playtime_data)
            else:
                # Создаем новую запись
                new_playtime = UserPlaytime(**playtime_data.model_dump())
                # session.add(new_playtime)
                created_playtimes.append(new_playtime)

        if created_playtimes:
            session.add_all(created_playtimes)

        # session.commit()
        # Обновляем объекты чтобы получить ID
        # for playtime in created_playtimes + updated_playtimes:
        #     session.refresh(playtime)

        return {
            'created': created_playtimes,
            'updated': updated_playtimes,
            'skipped': skipped_playtimes,
            'total_processed': len(playtimes_data),
            'total_created': len(created_playtimes),
            'total_updated': len(updated_playtimes)
        }

    def get_total_playtime(self, session: Session, user_id: int) -> int:
        """Получить общее время игры пользователя"""
        from sqlalchemy import func
        result = session.query(func.sum(UserPlaytime.playtime_forever)). \
            filter(UserPlaytime.user_id == user_id). \
            scalar()
        return result or 0


    # def get_recently_played_games(self, session: Session, user_id: int,
    #                               days: int = 30, limit: int = 50) -> List[UserPlaytime]:
    #     """Получить недавно сыгранные игры"""
    #     cutoff_date = datetime.utcnow() - timedelta(days=days)
    #
    #     return session.query(UserPlaytime). \
    #         filter(
    #         UserPlaytime.user_id == user_id,
    #         UserPlaytime.last_played >= cutoff_date
    #     ). \
    #         order_by(UserPlaytime.last_played.desc()). \
    #         limit(limit).all()