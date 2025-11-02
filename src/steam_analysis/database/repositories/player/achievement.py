from typing import List, Optional, Dict, Tuple, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload

from ..base.base import BaseDBRepository
from ...models import UserAchievement
from steam_analysis.core.schemas.player.playergame import AchievementCreate


class PlayerAchievementRepository(BaseDBRepository[UserAchievement, AchievementCreate, Any]):
    """Репозиторий для работы с достижениями пользователей"""

    def __init__(self):
        super().__init__(model=UserAchievement)

    def get_user_achievement(self, session: Session, user_id: int,
                             game_id: int, achievement_id: int) -> Optional[UserAchievement]:
        """Получить достижение пользователя"""
        return session.query(UserAchievement). \
            filter(
            UserAchievement.user_id == user_id,
            UserAchievement.game_id == game_id,
            UserAchievement.achievement_id == achievement_id
        ).first()

    def get_user_achievements(self, session: Session, user_id: int,
                              game_id: Optional[int] = None) -> List[UserAchievement]:
        """Получить достижения пользователя"""
        query = session.query(UserAchievement). \
            filter(UserAchievement.user_id == user_id)

        if game_id:
            query = query.filter(UserAchievement.game_id == game_id)

        return query.all()

    def create_or_update_achievement(self, session: Session,
                                     achievement_create: AchievementCreate) -> UserAchievement:
        """Создать или обновить достижение"""
        existing = self.get_user_achievement(
            session,
            achievement_create.user_id,
            achievement_create.game_id,
            achievement_create.achievement_id
        )

        if existing:
            # Обновляем существующее достижение
            for key, value in achievement_create.model_dump().items():
                if value is not None:
                    setattr(existing, key, value)
        else:
            # Создаем новое достижение
            existing = UserAchievement(**achievement_create.model_dump())
            session.add(existing)

        session.commit()
        session.refresh(existing)
        return existing

    def create_achievements_bulk(self, session: Session,
                                 achievements_data: List[AchievementCreate]) -> Dict[str, Any]:
        """Массовое создание/обновление достижений"""
        if not achievements_data:
            return {
                'created': [], 'updated': [], 'skipped': [],
                'total_processed': 0, 'total_created': 0, 'total_updated': 0
            }

        achievement_triples = [
            (ach.user_id, ach.game_id, ach.achievement_id)
            for ach in achievements_data
        ]
        existing_achievements = self.get_existing_achievements(session, achievement_triples)

        created = []
        updated = []
        skipped = []

        for achievement_data in achievements_data:
            key = (achievement_data.user_id, achievement_data.game_id, achievement_data.achievement_id)
            existing = existing_achievements.get(key)

            if existing:
                # Обновляем если есть изменения
                updated_fields = False
                for field in ['achieved', 'unlock_time', 'unlock_timestamp']:
                    new_value = getattr(achievement_data, field)
                    if new_value is not None and getattr(existing, field) != new_value:
                        setattr(existing, field, new_value)
                        updated_fields = True

                if updated_fields:
                    updated.append(existing)
                else:
                    skipped.append(achievement_data)
            else:
                new_achievement = UserAchievement(**achievement_data.model_dump())
                session.add(new_achievement)
                created.append(new_achievement)

        session.commit()

        for item in created + updated:
            session.refresh(item)

        return {
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'total_processed': len(achievements_data),
            'total_created': len(created),
            'total_updated': len(updated)
        }

    def get_existing_achievements(self, session: Session,
                                  achievement_triples: List[Tuple[int, int, int]]) -> \
            Dict[Tuple[int, int, int], UserAchievement]:
        """Получить существующие достижения"""
        if not achievement_triples:
            return {}

        conditions = []
        for user_id, game_id, achievement_id in achievement_triples:
            conditions.append(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.game_id == game_id,
                    UserAchievement.achievement_id == achievement_id
                )
            )

        query = select(UserAchievement).where(or_(*conditions))
        result = session.execute(query)
        existing = result.scalars().all()

        return {(ach.user_id, ach.game_id, ach.achievement_id): ach for ach in existing}

    def get_achievement_stats(self, session: Session, user_id: int,
                              game_id: Optional[int] = None) -> Dict[str, Any]:
        """Получить статистику достижений"""
        from sqlalchemy import func, Integer

        query = session.query(
            func.count(UserAchievement.id).label('total'),
            func.sum(func.cast(UserAchievement.achieved, Integer)).label('unlocked')
        ).filter(UserAchievement.user_id == user_id)

        if game_id:
            query = query.filter(UserAchievement.game_id == game_id)

        result = query.first()

        total = result.total or 0
        unlocked = result.unlocked or 0
        completion_rate = (unlocked / total * 100) if total > 0 else 0

        return {
            'total_achievements': total,
            'unlocked_achievements': unlocked,
            'completion_rate': round(completion_rate, 2)
        }
