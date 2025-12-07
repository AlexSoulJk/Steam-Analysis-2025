from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_, and_

from ..base.base import BaseDBRepository
from ...models import GameDeveloper
from steam_analysis.core.schemas.game.developer import GameDeveloperCreate


class GameDeveloperRepository(BaseDBRepository[GameDeveloper, GameDeveloperCreate, Any]):
    """Репозиторий для работы со связями игр и разработчиков"""

    def __init__(self):
        super().__init__(model=GameDeveloper)

    def get_existing_pairs(self, session: Session, pairs: List[Tuple[int, int]]) -> List[GameDeveloper]:
        """
        Получить существующие связи game_id - developer_id

        Args:
            pairs: Список кортежей (game_id, developer_id)

        Returns:
            Список существующих связей
        """
        if not pairs:
            return []

        conditions = []
        for game_id, developer_id in pairs:
            conditions.append(
                and_(
                    self.model.game_id == game_id,
                    self.model.developer_id == developer_id
                )
            )

        query = select(self.model).where(or_(*conditions))
        result = session.execute(query)
        return list(result.scalars().all())

    def create_bulk(self, session: Session, schemas: List[GameDeveloperCreate]) -> List[GameDeveloper]:
        """
        Массовое создание связей игр с разработчиками

        Args:
            pairs: Список кортежей (game_id, developer_id)

        Returns:
            Список созданных связей
        """
        pairs = [(schema.game_id, schema.developer_id) for schema in schemas]

        if not pairs:
            return []

        # Получаем существующие связи
        existing_relations = self.get_existing_pairs(session, pairs)
        existing_pairs = {
            (rel.game_id, rel.developer_id) for rel in existing_relations
        }

        # Фильтруем новые связи
        new_pairs = [
            (game_id, developer_id)
            for game_id, developer_id in pairs
            if (game_id, developer_id) not in existing_pairs
        ]

        if not new_pairs:
            return existing_relations

        # Создаем новые связи
        new_relations = []
        for game_id, developer_id in new_pairs:
            relation = GameDeveloper(
                game_id=game_id,
                developer_id=developer_id
            )
            new_relations.append(relation)

        session.add_all(new_relations)
        # session.commit()

        # for relation in new_relations:
        #     session.refresh(relation)

        return existing_relations + new_relations

    def get_by_game_id(self, session: Session, game_id: int) -> List[GameDeveloper]:
        """Получить все связи для конкретной игры"""
        query = select(self.model).where(self.model.game_id == game_id)
        result = session.execute(query)
        return list(result.scalars().all())

    def get_by_developer_id(self, session: Session, developer_id: int) -> List[GameDeveloper]:
        """Получить все связи для конкретного разработчика"""
        query = select(self.model).where(self.model.developer_id == developer_id)
        result = session.execute(query)
        return list(result.scalars().all())

    def get_developers_by_game_id(self, session: Session, game_id: int) -> List[Any]:
        """Получить разработчиков для конкретной игры (с join)"""
        from ...models import Developer

        query = select(Developer). \
            join(GameDeveloper, GameDeveloper.developer_id == Developer.id). \
            where(GameDeveloper.game_id == game_id)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_games_by_developer_id(self, session: Session, developer_id: int) -> List[Any]:
        """Получить игры для конкретного разработчика (с join)"""
        from ...models import Game

        query = select(Game). \
            join(GameDeveloper, GameDeveloper.game_id == Game.id). \
            where(GameDeveloper.developer_id == developer_id)

        result = session.execute(query)
        return list(result.scalars().all())

    def delete_by_game_id(self, session: Session, game_id: int) -> int:
        """Удалить все связи для конкретной игры"""
        deleted_count = session.query(self.model). \
            filter(self.model.game_id == game_id). \
            delete(synchronize_session=False)

        # session.commit()
        return deleted_count

    def delete_by_developer_id(self, session: Session, developer_id: int) -> int:
        """Удалить все связи для конкретного разработчика"""
        deleted_count = session.query(self.model). \
            filter(self.model.developer_id == developer_id). \
            delete(synchronize_session=False)

        # session.commit()
        return deleted_count