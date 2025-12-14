from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_, and_

from ..base.base import BaseDBRepository
from ...models import Developer, Publisher, GameDeveloper, GamePublisher
from steam_analysis.core.schemas.game.developer import DeveloperCreate
from steam_analysis.core.schemas.game.developer import PublisherCreate


class PublisherRepository(BaseDBRepository[Publisher, PublisherCreate, Any]):
    """Репозиторий для работы с издателями"""

    def __init__(self):
        super().__init__(model=Publisher)

    def get_by_name(self, name: str, session: Session) -> Optional[Publisher]:
        """Получить издателя по имени"""
        return self.get_by_field("name", name, session=session)

    def get_existing_by_names(self, names: List[str], session: Session) -> Dict[str, Publisher]:
        """
        Получить существующих издателей по списку names одним запросом
        Возвращает словарь {name: publisher_object}
        """
        if not names:
            return {}

        query = select(self.model).where(self.model.name.in_(names))
        result = session.execute(query)
        existing_publishers = result.scalars().all()

        return {publisher.name: publisher for publisher in existing_publishers}

    def create_bulk(self, objects_in: List[PublisherCreate], session: Session) -> List[Publisher]:
        """
        Массовое создание издателей

        Args:
            objects_in: Список Pydantic схем

        Returns:
            Список созданных издателей
        """
        db_objects = []
        names = list(map(lambda x: x.name, objects_in))
        existing_pubs_map = self.get_existing_by_names(names, session)

        new_pubs = [
            obj for obj in objects_in
            if obj.name not in existing_pubs_map
        ]

        existing_pubs = list(existing_pubs_map.values())

        if not new_pubs:
            return existing_pubs

        for obj_in in new_pubs:
            obj_data = obj_in.model_dump(by_alias=True) if hasattr(obj_in, 'model_dump') else obj_in.dict()
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        session.add_all(db_objects)
        # session.commit()

        # for db_obj in db_objects:
        #     session.refresh(db_obj)

        return existing_pubs + db_objects

    def get_with_games(self, session: Session, publisher_id: int) -> Optional[Publisher]:
        """TODO: Получить издателя со всеми связанными играми"""
        return session.query(Publisher). \
            options(
            joinedload(Publisher.games).joinedload("game")
        ). \
            filter(Publisher.id == publisher_id). \
            first()

    def search_by_name(self, session: Session, search_term: str,
                       skip: int = 0, limit: int = 100) -> List[Publisher]:
        """Поиск издателей по имени (регистронезависимый)"""
        query = session.query(Publisher). \
            filter(Publisher.name.ilike(f"%{search_term}%")). \
            offset(skip).limit(limit)

        return query.all()

    def get_top_publishers(self, session: Session, limit: int = 10) -> List[Publisher]:
        """Получить топ издателей"""
        query = session.query(Publisher). \
            order_by(Publisher.created_at.desc()). \
            limit(limit)

        return query.all()

    def get_developers_publishers_by_games(self, session: Session, game_ids: List[int]) -> Dict[str, List]:
        """
        Получить разработчиков и издателей для списка игр

        Returns:
            Словарь с ключами 'developers' и 'publishers'
        """

        if not game_ids:
            return {'developers': [], 'publishers': []}

        # Получаем разработчиков
        dev_query = session.query(Developer). \
            join(GameDeveloper, GameDeveloper.developer_id == Developer.id). \
            filter(GameDeveloper.game_id.in_(game_ids)). \
            distinct()

        developers = dev_query.all()

        # Получаем издателей
        pub_query = session.query(Publisher). \
            join(GamePublisher, GamePublisher.publisher_id == Publisher.id). \
            filter(GamePublisher.game_id.in_(game_ids)). \
            distinct()

        publishers = pub_query.all()

        return {
            'developers': developers,
            'publishers': publishers
        }
