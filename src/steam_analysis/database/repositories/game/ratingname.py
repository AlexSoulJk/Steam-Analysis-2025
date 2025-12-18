from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..base.base import BaseDBRepository
from ...models.game import Rating, RatingNames
from steam_analysis.core.schemas.game.ratings import RatingNameCreate


class RatingNameRepository(BaseDBRepository[RatingNames, RatingNameCreate, Any]):
    """Репозиторий для работы с названиями рейтинговых систем (usk, agcom, steam_germany и т.д.)"""

    def __init__(self):
        super().__init__(model=RatingNames)

    def get_by_description(self, description: str, session: Session) -> Optional[RatingNames]:
        """Получить рейтинговую систему по описанию (например, 'usk')"""
        return self.get_by_field("description", description, session=session)

    def get_existing_by_descriptions(self, descriptions: List[str], session: Session) -> Dict[str, RatingNames]:
        """
        Получить существующие рейтинговые системы по списку descriptions одним запросом
        Возвращает словарь {description: rating_name_object}
        """
        if not descriptions:
            return {}

        stmt = select(self.model).where(self.model.description.in_(descriptions))
        result = session.execute(stmt)
        existing_names = result.scalars().all()

        return {rating_name.description: rating_name for rating_name in existing_names}

    def create_bulk(self, objects_in: List[RatingNameCreate], session: Session) -> List[RatingNames]:
        """
        Массовое создание названий рейтинговых систем

        Args:
            objects_in: Список Pydantic схем RatingNameCreate
            session: Сессия SQLAlchemy

        Returns:
            Список созданных и существующих рейтинговых систем
        """
        db_objects = []
        descriptions = [obj.description for obj in objects_in]
        existing_names_map = self.get_existing_by_descriptions(descriptions, session)

        new_names = [
            obj for obj in objects_in
            if obj.description not in existing_names_map
        ]

        existing_names = list(existing_names_map.values())

        if not new_names:
            return existing_names

        for obj_in in new_names:
            obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        session.add_all(db_objects)
        return existing_names + db_objects

    def get_ratings_by_name(self, rating_name_id: int, session: Session) -> List[Rating]:
        """Получить все рейтинги для конкретной рейтинговой системы"""
        stmt = select(Rating).where(Rating.rating_name_id == rating_name_id)
        result = session.execute(stmt)
        return list(result.scalars().all())
