from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from ..base.base import BaseDBRepository
from ...models.game import Rating
from steam_analysis.core.schemas.game.ratings import RatingCreate


class RatingRepository(BaseDBRepository[Rating, RatingCreate, Any]):
    """Репозиторий для работы с рейтингами игр"""

    def __init__(self):
        super().__init__(model=Rating)
        self._batch_size = 1000  # Размер батча для запросов

    def get_existing_by_game_and_names(self, game_id: int, rating_name_ids: List[int],
                                       session: Session) -> Dict[int, Rating]:
        """
        Получить существующие рейтинги для конкретной игры по списку rating_name_ids
        Возвращает словарь {rating_name_id: rating_object}
        """
        if not rating_name_ids:
            return {}

        result_dict = {}
        # Батчинг для избежания ошибки "too many parameters"
        for i in range(0, len(rating_name_ids), self._batch_size):
            batch = rating_name_ids[i:i + self._batch_size]

            stmt = select(self.model).where(
                self.model.game_id == game_id,
                self.model.rating_name_id.in_(batch) if len(batch) > 1
                else self.model.rating_name_id == batch[0]
            )
            result = session.execute(stmt)
            batch_ratings = result.scalars().all()

            for rating in batch_ratings:
                result_dict[rating.rating_name_id] = rating

        return result_dict

    def get_existing_pairs(self, session: Session, pairs: List[Tuple[int, int]], batch_size: int = 500) -> List[Rating]:
        """
        Получить существующие связи game_id - rating_name_id с батчингом

        Args:
            pairs: Список кортежей (game_id, rating_name_id)
            batch_size: Размер батча для запросов (по умолчанию 500)

        Returns:
            Список существующих связей
        """
        if not pairs:
            return []

        all_existing = []

        # Обрабатываем пары батчами
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]

            # Создаем OR-условия для текущего батча
            conditions = []
            for game_id, rating_name_id in batch:
                conditions.append(
                    and_(
                        self.model.game_id == game_id,
                        self.model.rating_name_id == rating_name_id
                    )
                )

            # Выполняем запрос для текущего батча
            if conditions:
                stmt = select(self.model).where(or_(*conditions))
                result = session.execute(stmt)
                batch_existing = list(result.scalars().all())
                all_existing.extend(batch_existing)

        return all_existing

    def create_bulk(self, schemas: List[RatingCreate], session: Session) -> List[Rating]:
        """
        Массовое создание рейтингов

        Args:
            schemas: Список Pydantic схем RatingCreate

        Returns:
            Список созданных и существующих рейтингов
        """
        pairs = [(schema.game_id, schema.rating_name_id) for schema in schemas]

        if not pairs:
            return []

        existing_ratings = self.get_existing_pairs(session, pairs)

        # Создаем множество для быстрой проверки
        existing_pairs_set = {
            (rating.game_id, rating.rating_name_id) for rating in existing_ratings
        }

        new_schemas = []
        for schema in schemas:
            pair_key = (schema.game_id, schema.rating_name_id)
            if pair_key not in existing_pairs_set:
                new_schemas.append(schema)

        if not new_schemas:
            return existing_ratings

        new_ratings = []
        for schema in new_schemas:
            try:
                # Преобразуем схему в словарь
                if hasattr(schema, 'model_dump'):
                    obj_data = schema.model_dump()
                else:
                    obj_data = schema.dict()

                rating = Rating(**obj_data)
                new_ratings.append(rating)

            except Exception as e:
                print(f"Ошибка при создании рейтинга для игры {schema.game_id}, "
                      f"rating_name_id {schema.rating_name_id}: {e}")
                continue

        if not new_ratings:
            return existing_ratings

        session.add_all(new_ratings)

        return existing_ratings + new_ratings

    def get_ratings_by_game(self, game_id: int, session: Session) -> List[Rating]:
        """Получить все рейтинги для конкретной игры"""
        stmt = select(self.model).where(self.model.game_id == game_id)
        result = session.execute(stmt)
        return list(result.scalars().all())

    def get_ratings_by_game_with_names(self, game_id: int, session: Session) -> List[Dict[str, Any]]:
        """
        Получить все рейтинги для игры с именами рейтинговых систем
        Возвращает список словарей с полной информацией
        """
        from sqlalchemy.orm import joinedload

        stmt = (
            select(self.model)
            .options(joinedload(self.model.rating_name))
            .where(self.model.game_id == game_id)
        )
        result = session.execute(stmt)
        ratings = result.scalars().unique().all()

        return [
            {
                'id': rating.id,
                'rating': rating.rating,
                'req_age': rating.req_age,
                'banned': rating.banned,
                'rating_name': rating.rating_name.description,
                'rating_name_id': rating.rating_name_id
            }
            for rating in ratings
        ]
