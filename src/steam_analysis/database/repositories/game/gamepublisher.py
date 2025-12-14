from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_, and_

from ..base.base import BaseDBRepository
from ...models import GamePublisher
from steam_analysis.core.schemas.game.developer import GamePublisherCreate


class GamePublisherRepository(BaseDBRepository[GamePublisher, GamePublisherCreate, Any]):
    """Репозиторий для работы со связями игр и издателей"""

    def __init__(self):
        super().__init__(model=GamePublisher)

    def get_existing_pairs(self, session: Session, pairs: List[Tuple[int, int]]) -> List[GamePublisher]:
        """
        Получить существующие связи game_id - publisher_id
        """
        if not pairs:
            return []

        conditions = []
        for game_id, publisher_id in pairs:
            conditions.append(
                and_(
                    self.model.game_id == game_id,
                    self.model.publisher_id == publisher_id
                )
            )

        query = select(self.model).where(or_(*conditions))
        result = session.execute(query)
        return list(result.scalars().all())

    def create_bulk(self, schemas: List[GamePublisherCreate], session: Session) -> List[GamePublisher]:
        """
        Массовое создание связей игр с издателями
        """
        pairs = [(schema.game_id, schema.publisher_id) for schema in schemas]
        if not pairs:
            return []

        # Получаем существующие связи
        existing_relations = self.get_existing_pairs(session, pairs)
        existing_pairs = {
            (rel.game_id, rel.publisher_id) for rel in existing_relations
        }

        # Фильтруем новые связи
        new_pairs = [
            (game_id, publisher_id)
            for game_id, publisher_id in pairs
            if (game_id, publisher_id) not in existing_pairs
        ]

        if not new_pairs:
            return existing_relations

        # Создаем новые связи
        new_relations = []
        for game_id, publisher_id in new_pairs:
            relation = GamePublisher(
                game_id=game_id,
                publisher_id=publisher_id
            )
            new_relations.append(relation)

        session.add_all(new_relations)
        # session.commit()

        # for relation in new_relations:
        #     session.refresh(relation)

        return existing_relations + new_relations

    def get_by_game_id(self, session: Session, game_id: int) -> List[GamePublisher]:
        """Получить все связи для конкретной игры"""
        query = select(self.model).where(self.model.game_id == game_id)
        result = session.execute(query)
        return list(result.scalars().all())

    def get_by_publisher_id(self, session: Session, publisher_id: int) -> List[GamePublisher]:
        """Получить все связи для конкретного издателя"""
        query = select(self.model).where(self.model.publisher_id == publisher_id)
        result = session.execute(query)
        return list(result.scalars().all())

    def get_publishers_by_game_id(self, session: Session, game_id: int) -> List[Any]:
        """Получить издателей для конкретной игры (с join)"""
        from ...models import Publisher

        query = select(Publisher). \
            join(GamePublisher, GamePublisher.publisher_id == Publisher.id). \
            where(GamePublisher.game_id == game_id)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_games_by_publisher_id(self, session: Session, publisher_id: int) -> List[Any]:
        """Получить игры для конкретного издателя (с join)"""
        from ...models import Game

        query = select(Game). \
            join(GamePublisher, GamePublisher.game_id == Game.id). \
            where(GamePublisher.publisher_id == publisher_id)

        result = session.execute(query)
        return list(result.scalars().all())

    def delete_by_game_id(self, session: Session, game_id: int) -> int:
        """Удалить все связи для конкретной игры"""
        deleted_count = session.query(self.model). \
            filter(self.model.game_id == game_id). \
            delete(synchronize_session=False)

        # session.commit()
        return deleted_count

    def delete_by_publisher_id(self, session: Session, publisher_id: int) -> int:
        """Удалить все связи для конкретного издателя"""
        deleted_count = session.query(self.model). \
            filter(self.model.publisher_id == publisher_id). \
            delete(synchronize_session=False)

        # session.commit()
        return deleted_count