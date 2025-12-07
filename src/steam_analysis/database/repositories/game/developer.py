from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_, and_

from ..base.base import BaseDBRepository
from ...models import Developer, Publisher, GameDeveloper, GamePublisher
from steam_analysis.core.schemas.game.developer import DeveloperCreate
from steam_analysis.core.schemas.game.developer import PublisherCreate


class DeveloperRepository(BaseDBRepository[Developer, DeveloperCreate, Any]):
    """Репозиторий для работы с разработчиками"""

    def __init__(self):
        super().__init__(model=Developer)

    def get_by_name(self, name: str, session: Session) -> Optional[Developer]:
        """Получить разработчика по имени"""
        return self.get_by_field("name", name, session=session)

    def get_existing_by_names(self, names: List[str], session: Session) -> Dict[str, Developer]:
        """
        Получить существующих разработчиков по списку names одним запросом
        Возвращает словарь {name: developer_object}
        """
        if not names:
            return {}

        query = select(self.model).where(self.model.name.in_(names))
        result = session.execute(query)
        existing_developers = result.scalars().all()

        return {developer.name: developer for developer in existing_developers}

    def create_bulk(self, objects_in: List[DeveloperCreate], session: Session) -> List[Developer]:
        """
        Массовое создание разработчиков

        Args:
            objects_in: Список Pydantic схем

        Returns:
            Список созданных разработчиков
        """
        db_objects = []
        names = list(map(lambda x: x.name, objects_in))
        existing_devs_map = self.get_existing_by_names(names, session)

        new_devs = [
            obj for obj in objects_in
            if obj.name not in existing_devs_map
        ]

        existing_devs = list(existing_devs_map.values())

        if not new_devs:
            return existing_devs

        for obj_in in new_devs:
            obj_data = obj_in.model_dump(by_alias=True) if hasattr(obj_in, 'model_dump') else obj_in.dict()
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        session.add_all(db_objects)
        # session.commit()

        # for db_obj in db_objects:
        #     session.refresh(db_obj)

        return existing_devs + db_objects

    def get_with_games(self, session: Session, developer_id: int) -> Optional[Developer]:
        """Получить разработчика со всеми связанными играми"""
        return session.query(Developer). \
            options(
            joinedload(Developer.games).joinedload("game")
        ). \
            filter(Developer.id == developer_id). \
            first()

    def search_by_name(self, session: Session, search_term: str,
                       skip: int = 0, limit: int = 100) -> List[Developer]:
        """Поиск разработчиков по имени (регистронезависимый)"""
        query = session.query(Developer). \
            filter(Developer.name.ilike(f"%{search_term}%")). \
            offset(skip).limit(limit)

        return query.all()

    def get_top_developers(self, session: Session, limit: int = 10) -> List[Developer]:
        """Получить топ разработчиков (можно расширить логикой подсчета игр)"""
        # Пример: просто возвращаем последних добавленных
        query = session.query(Developer). \
            order_by(Developer.created_at.desc()). \
            limit(limit)

        return query.all()


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

    def create_bulk(self, session: Session, pairs: List[Tuple[int, int]]) -> List[GameDeveloper]:
        """
        Массовое создание связей игр с разработчиками

        Args:
            pairs: Список кортежей (game_id, developer_id)

        Returns:
            Список созданных связей
        """
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

    def create_bulk_from_schemas(self, session: Session,
                                 schemas: List[GameDeveloperCreate]) -> List[GameDeveloper]:
        """
        Массовое создание связей из Pydantic схем
        """
        pairs = [(schema.game_id, schema.developer_id) for schema in schemas]
        return self.create_bulk(session, pairs)

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