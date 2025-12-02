from typing import Optional, List, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas import GameCreate, GameUpdate

from ..base.base import BaseDBRepository
from ...models import Game
from ...models.game import GameGenre, GameCategory, GamePlatform


class GameRepository(BaseDBRepository[Game, GameCreate, GameUpdate]):
    """Репозиторий для работы с играми"""

    def __init__(self):
        super().__init__(model=Game)

    def get_by_app_id(self, app_id: int, session: Session) -> Optional[Game]:
        return self.get_by_field("app_id",
                                 app_id,
                                 session=session)

    def get_existing_by_app_ids(self, app_ids: List[int], session: Session) -> Dict[int, Game]:
        """
        Получить существующие игры по списку app_ids одним запросом
        Возвращает словарь {app_id: game_object}
        """
        if not app_ids:
            return {}

        query = select(self.model).where(self.model.app_id.in_(app_ids))
        result = session.execute(query)
        existing_games = result.scalars().all()

        return {game.app_id: game for game in existing_games}

    def count_games_by_categories_for_type(
            self,
            session: Session,
            type_id: int = 1
    ) -> List[Tuple[str, int]]:
        from ...models.game import Category, GameCategory

        """
        Подсчитать количество игр по категориям для типа type_id

        Args:
            session: SQLAlchemy сессия
            type_id: ID типа игры

        Returns:
            Список кортежей (название_категории, количество_игр)
        """
        # Для связи Game -> Category нам нужен промежуточный JOIN через GameCategory
        # Сначала JOIN Game -> GameCategory, потом GameCategory -> Category

        additional_joins = [
            (GameCategory, Game.id == GameCategory.game_id),
            (Category, GameCategory.category_id == Category.id)
        ]

        # Используем базовый метод
        results = self.count_with_join_group_by(
            session=session,
            join_model=GameCategory,  # Первый JOIN
            join_condition=Game.id == GameCategory.game_id,
            group_by_field='category_id',  # Группируем по названию категории
            count_field='id',
            filters={'type_id': type_id},
            additional_joins=[
            # Второй JOIN: GameCategory → Category
            (Category, GameCategory.category_id == Category.id)
        ]
        )

        return results

    def create_bulk(self, objects_in: List[GameCreate], session: Session) -> List[Game]:
        """
        Массовое создание объектов

        Args:
            objects_in: Список Pydantic схем

        Returns:
            Список созданных объектов
        """
        db_objects = []
        app_ids = list(map(lambda x: x.app_id, objects_in))
        existing_games_map = self.get_existing_by_app_ids(app_ids, session)

        new_games = [
            obj for obj in objects_in
            if obj.app_id not in existing_games_map
        ]

        existing_games = list(existing_games_map.values())

        if not new_games:
            return existing_games

        for obj_in in new_games:
            # Стоит ли так оставлять?? с alias в качестве жестко захоровоженного
            obj_data = obj_in.model_dump(by_alias=True) if hasattr(obj_in, 'model_dump') else obj_in.dict()
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        session.add_all(db_objects)
        session.commit()

        # Обновляем объекты, чтобы получить их ID
        for db_obj in db_objects:
            session.refresh(db_obj)

        return existing_games + db_objects

    def get_with_details(self, session: Session, game_id: int) -> Optional[Game]:
        """Получить игру со всеми связанными данными"""
        return session.query(Game). \
            options(
            joinedload(Game.game_type),
            joinedload(Game.metrics),
            joinedload(Game.genres).joinedload(GameGenre.genre),
            joinedload(Game.categories).joinedload(GameCategory.category),
            joinedload(Game.platforms).joinedload(GamePlatform.platform),
            joinedload(Game.prices)
        ). \
            filter(Game.id == game_id). \
            first()

    def get_free_games(self, session: Session, skip: int = 0, limit: int = 100) -> List[Game]:
        """Получить бесплатные игры"""
        return self.get_multi(skip=skip, limit=limit, filters={"is_free": True}, session=session)

    def get_upcoming_games(self, session: Session, skip: int = 0, limit: int = 100) -> List[Game]:
        """Получить предстоящие игры"""
        return self.get_multi(skip=skip, limit=limit, filters={"coming_soon": True}, session=session)

    def search_by_name(self, session: Session, name: str, skip: int = 0, limit: int = 100) -> List[Game]:
        """Поиск игр по названию"""
        return session.query(Game). \
            filter(Game.name.ilike(f"%{name}%")). \
            offset(skip).limit(limit).all()

    def get_last_uploaded_game(self, session: Session) -> Optional[Game]:
        """Получить последнюю загруженную игру по app_id"""
        return session.query(Game). \
            order_by(Game.app_id.desc()). \
            first()
