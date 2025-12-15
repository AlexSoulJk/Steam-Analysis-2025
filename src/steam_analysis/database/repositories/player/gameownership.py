from typing import Optional, List, Dict, Tuple, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime

from ..base.base import BaseDBRepository
from ...models import UserGameOwnership, Game
from steam_analysis.core.schemas.player.playergame import OwnershipCreate


class PlayerGameOwnershipRepository(BaseDBRepository[UserGameOwnership, OwnershipCreate, Any]):
    """Репозиторий для работы с владением играми"""

    def __init__(self):
        super().__init__(model=UserGameOwnership)

    def get_ownership(self, session: Session, user_id: int, game_id: int) -> Optional[UserGameOwnership]:
        """Получить владение игрой"""
        return session.query(UserGameOwnership). \
            filter(
            UserGameOwnership.user_id == user_id,
            UserGameOwnership.game_id == game_id
        ).first()

    def get_user_owned_games(self, session: Session, user_id: int) -> List[UserGameOwnership]:
        """Получить все игры пользователя"""
        return session.query(UserGameOwnership). \
            filter(
            UserGameOwnership.user_id == user_id,
            UserGameOwnership.owned == True
        ).all()

    def create_or_update_ownership(self, session: Session,
                                   ownership_create: OwnershipCreate) -> UserGameOwnership:
        """Создать или обновить владение игрой"""
        existing = self.get_ownership(
            session,
            ownership_create.user_id,
            ownership_create.game_id
        )

        if existing:
            existing.owned = ownership_create.owned
        else:
            existing = UserGameOwnership(**ownership_create.model_dump())
            session.add(existing)

        # session.commit()
        # session.refresh(existing)
        return existing

    def create_ownerships_bulk(self, session: Session,
                               ownerships_data: List[OwnershipCreate]) -> Dict[str, Any]:
        """Массовое создание/обновление владений играми"""
        if not ownerships_data:
            return {
                'created': [], 'updated': [], 'skipped': [],
                'total_processed': 0, 'total_created': 0, 'total_updated': 0
            }

        ownership_pairs = [(own.user_id, own.game_id) for own in ownerships_data]
        existing_ownerships = self.get_existing_ownerships(session, ownership_pairs)

        created = []
        updated = []
        skipped = []

        for ownership_data in ownerships_data:
            user_id = ownership_data.user_id
            game_id = ownership_data.game_id

            existing = existing_ownerships.get((user_id, game_id))

            if existing:
                # Обновляем только если изменилось значение owned
                if existing.owned != ownership_data.owned:
                    existing.owned = ownership_data.owned
                    updated.append(existing)
                else:
                    skipped.append(ownership_data)
            else:
                new_ownership = UserGameOwnership(**ownership_data.model_dump())
                # session.add(new_ownership)
                created.append(new_ownership)

        session.add_all(created)
        # session.commit()
        #
        # for item in created + updated:
        #     session.refresh(item)

        return {
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'total_processed': len(ownerships_data),
            'total_created': len(created),
            'total_updated': len(updated)
        }

    def get_existing_ownerships(self, session: Session,
                                ownership_pairs: List[Tuple[int, int]]) -> Dict[Tuple[int, int], UserGameOwnership]:
        """Получить существующие владения"""
        if not ownership_pairs:
            return {}

        result_dict = {}
        batch_size = 100

        for i in range(0, len(ownership_pairs), batch_size):
            batch = ownership_pairs[i:i + batch_size]

            conditions = []
            for user_id, game_id in batch:
                conditions.append(
                    and_(UserGameOwnership.user_id == user_id, UserGameOwnership.game_id == game_id)
                )

            query = select(UserGameOwnership).where(or_(*conditions))
            batch_result = session.execute(query)
            batch_existing = batch_result.scalars().all()

            for own in batch_existing:
                result_dict[(own.user_id, own.game_id)] = own

        return result_dict

        # conditions = []
        # for user_id, game_id in ownership_pairs:
        #     conditions.append(
        #         and_(UserGameOwnership.user_id == user_id, UserGameOwnership.game_id == game_id)
        #     )
        #
        # query = select(UserGameOwnership).where(or_(*conditions))
        # result = session.execute(query)
        # existing = result.scalars().all()
        #
        # return {(own.user_id, own.game_id): own for own in existing}

    def get_owned_games_count(self, session: Session, user_id: int) -> int:
        """Получить количество игр пользователя"""
        return session.query(UserGameOwnership). \
            filter(
            UserGameOwnership.user_id == user_id,
            UserGameOwnership.owned == True
        ).count()