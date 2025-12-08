# repositories/review_repository.py
from typing import Optional, List, Dict, Tuple, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, or_, desc, asc, func
from datetime import datetime, timedelta

from ..base.base import BaseDBRepository
from ...models import Review, User, Game
from steam_analysis.core.schemas.player.playergame import (
    ReviewCreate
)


class ReviewRepository(BaseDBRepository[Review, ReviewCreate, Any]):
    """Репозиторий для работы с отзывами пользователей"""

    def __init__(self):
        super().__init__(model=Review)

    def get_by_recommendation_id(self, session: Session, recommendation_id: str) -> Optional[Review]:
        """Получить отзыв по recommendation_id"""
        return self.get_by_field("recommendation_id", recommendation_id, session=session)

    def get_by_steam_id(self, session: Session, steam_id: str) -> List[Review]:
        """Получить отзывы по Steam ID пользователя"""
        query = select(self.model).where(self.model.steam_id == steam_id)
        result = session.execute(query)
        return list(result.scalars().all())

    def get_by_game_id(self, session: Session, game_id: int,
                       skip: int = 0, limit: int = 100,
                       order_by: str = 'newest') -> List[Review]:
        """Получить отзывы для конкретной игры"""
        query = select(self.model).where(self.model.game_id == game_id)

        # Сортировка
        if order_by == 'newest':
            query = query.order_by(desc(self.model.timestamp_created))
        elif order_by == 'oldest':
            query = query.order_by(asc(self.model.timestamp_created))
        elif order_by == 'most_helpful':
            query = query.order_by(desc(self.model.votes_up))
        elif order_by == 'most_funny':
            query = query.order_by(desc(self.model.votes_funny))

        query = query.offset(skip).limit(limit)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_by_user_id(self, session: Session, user_id: int,
                       skip: int = 0, limit: int = 100) -> List[Review]:
        """Получить отзывы по user_id (если есть связь)"""
        query = select(self.model). \
            where(self.model.user_id == user_id). \
            order_by(desc(self.model.timestamp_created)). \
            offset(skip).limit(limit)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_existing_by_recommendation_ids(self, session: Session,
                                           recommendation_ids: List[str]) -> Dict[str, Review]:
        """
        Получить существующие отзывы по списку recommendation_ids одним запросом

        Returns:
            Словарь {recommendation_id: review_object}
        """
        if not recommendation_ids:
            return {}

        query = select(self.model).where(self.model.recommendation_id.in_(recommendation_ids))
        result = session.execute(query)
        existing_reviews = result.scalars().all()

        return {review.recommendation_id: review for review in existing_reviews}

    def create_bulk(self, session: Session, reviews_in: List[ReviewCreate]) -> List[Review]:
        """
        Массовое создание отзывов

        Args:
            reviews_in: Список Pydantic схем отзывов

        Returns:
            Список созданных отзывов
        """
        if not reviews_in:
            return []

        # Получаем существующие отзывы
        recommendation_ids = [review.recommendation_id for review in reviews_in]
        existing_reviews_map = self.get_existing_by_recommendation_ids(session, recommendation_ids)

        # Фильтруем новые отзывы
        new_reviews = [
            review for review in reviews_in
            if review.recommendation_id not in existing_reviews_map
        ]

        existing_reviews = list(existing_reviews_map.values())

        if not new_reviews:
            return existing_reviews

        # Создаем новые отзывы
        db_objects = []
        for review_in in new_reviews:
            review_data = review_in.model_dump(exclude_unset=True)
            db_obj = self.model(**review_data)
            db_objects.append(db_obj)

        session.add_all(db_objects)
        # session.commit()

        # for db_obj in db_objects:
        #     session.refresh(db_obj)

        return existing_reviews + db_objects

    def get_with_user_and_game(self, session: Session, review_id: int) -> Optional[Review]:
        """Получить отзыв с данными пользователя и игры"""
        return session.query(self.model). \
            options(
            joinedload(self.model.user),
            joinedload(self.model.game)
        ). \
            filter(self.model.id == review_id). \
            first()

    def get_reviews_with_details(self, session: Session,
                                 game_id: Optional[int] = None,
                                 user_id: Optional[int] = None,
                                 skip: int = 0, limit: int = 100) -> List[Review]:
        """Получить отзывы с деталями пользователя и игры"""
        query = session.query(self.model). \
            options(
            joinedload(self.model.user),
            joinedload(self.model.game)
        )

        # Фильтры
        if game_id:
            query = query.filter(self.model.game_id == game_id)
        if user_id:
            query = query.filter(self.model.user_id == user_id)

        query = query.order_by(desc(self.model.timestamp_created)). \
            offset(skip).limit(limit)

        return query.all()

    def get_positive_reviews(self, session: Session, game_id: int,
                             min_votes_up: int = 0,
                             skip: int = 0, limit: int = 100) -> List[Review]:
        """Получить положительные отзывы для игры"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.voted_up == True,
                self.model.votes_up >= min_votes_up
            )
        ). \
            order_by(desc(self.model.votes_up)). \
            offset(skip).limit(limit)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_negative_reviews(self, session: Session, game_id: int,
                             min_votes_up: int = 0,
                             skip: int = 0, limit: int = 100) -> List[Review]:
        """Получить отрицательные отзывы для игры"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.voted_up == False,
                self.model.votes_up >= min_votes_up
            )
        ). \
            order_by(desc(self.model.votes_up)). \
            offset(skip).limit(limit)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_reviews_by_language(self, session: Session, game_id: int,
                                language: str,
                                skip: int = 0, limit: int = 100) -> List[Review]:
        """Получить отзывы на определенном языке"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.language == language
            )
        ). \
            order_by(desc(self.model.timestamp_created)). \
            offset(skip).limit(limit)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_reviews_by_vote_score_range(self, session: Session,
                                        min_score: float,
                                        max_score: Optional[float] = None,
                                        skip: int = 0, limit: int = 100) -> List[Review]:
        """Получить отзывы по диапазону weighted_vote_score"""
        query = select(self.model). \
            where(self.model.weighted_vote_score >= min_score)

        if max_score is not None:
            query = query.where(self.model.weighted_vote_score <= max_score)

        query = query.order_by(desc(self.model.weighted_vote_score)). \
            offset(skip).limit(limit)

        result = session.execute(query)
        return list(result.scalars().all())


