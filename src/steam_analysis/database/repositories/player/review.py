from typing import List, Optional, Dict, Tuple, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload

from ..base.base import BaseDBRepository
from ...models import Review
from steam_analysis.core.schemas.player.playergame import ReviewCreate


class ReviewRepository(BaseDBRepository[Review, ReviewCreate, Any]):
    """Репозиторий для работы с отзывами"""

    def __init__(self):
        super().__init__(model=Review)

    def get_by_recommendation_id(self, session: Session,
                                 recommendation_id: str) -> Optional[Review]:
        """Получить отзыв по recommendation_id"""
        return session.query(Review). \
            filter(Review.recommendation_id == recommendation_id). \
            first()

    def get_game_reviews(self, session: Session, game_id: int,
                         skip: int = 0, limit: int = 100) -> List[Review]:
        """Получить отзывы на игру"""
        return session.query(Review). \
            filter(Review.game_id == game_id). \
            offset(skip).limit(limit).all()

    def get_user_reviews(self, session: Session, user_id: int,
                         skip: int = 0, limit: int = 100) -> List[Review]:
        """Получить отзывы пользователя"""
        return session.query(Review). \
            filter(Review.user_id == user_id). \
            offset(skip).limit(limit).all()

    def create_or_update_review(self, session: Session,
                                review_create: ReviewCreate) -> Review:
        """Создать или обновить отзыв"""
        existing = self.get_by_recommendation_id(
            session,
            review_create.recommendation_id
        )

        if existing:
            # Обновляем существующий отзыв
            for key, value in review_create.model_dump().items():
                if value is not None:
                    setattr(existing, key, value)
        else:
            # Создаем новый отзыв
            existing = Review(**review_create.model_dump())
            session.add(existing)

        # session.commit()
        # session.refresh(existing)
        return existing

    def create_reviews_bulk(self, session: Session,
                            reviews_data: List[ReviewCreate]) -> Dict[str, Any]:
        """Массовое создание/обновление отзывов"""
        if not reviews_data:
            return {
                'created': [],
                'updated': [],
                'skipped': [],
                'total_processed': 0,
                'total_created': 0,
                'total_updated': 0
            }

        # Собираем все recommendation_id для проверки
        recommendation_ids = [review.recommendation_id for review in reviews_data]

        # Получаем существующие отзывы за один запрос
        existing_reviews = self.get_existing_reviews_by_recommendation_ids(session, recommendation_ids)

        created_reviews = []
        updated_reviews = []
        skipped_reviews = []

        for review_data in reviews_data:
            recommendation_id = review_data.recommendation_id
            existing_review = existing_reviews.get(recommendation_id)

            if existing_review:
                # Обновляем существующий отзыв
                updated = False
                for key, value in review_data.model_dump().items():
                    # Пропускаем поля, которые не должны обновляться
                    if key in ['recommendation_id', 'steam_id']:
                        continue

                    if value is not None and getattr(existing_review, key) != value:
                        setattr(existing_review, key, value)
                        updated = True

                if updated:
                    updated_reviews.append(existing_review)
                else:
                    skipped_reviews.append(review_data)
            else:
                # Создаем новый отзыв
                new_review = Review(**review_data.model_dump())
                # session.add(new_review)
                created_reviews.append(new_review)

        if created_reviews:
            session.add_all(created_reviews)
        # session.commit()
        #
        # # Обновляем объекты чтобы получить ID
        # for review in created_reviews + updated_reviews:
        #     session.refresh(review)

        return {
            'created': created_reviews,
            'updated': updated_reviews,
            'skipped': skipped_reviews,
            'total_processed': len(reviews_data),
            'total_created': len(created_reviews),
            'total_updated': len(updated_reviews)
        }

    def get_existing_reviews_by_recommendation_ids(self, session: Session,
                                                   recommendation_ids: List[str]) -> Dict[str, Review]:
        """
        Получить существующие отзывы по recommendation_id
        Возвращает словарь {recommendation_id: review_object}
        """
        if not recommendation_ids:
            return {}

        query = select(Review).where(Review.recommendation_id.in_(recommendation_ids))
        result = session.execute(query)
        existing_reviews = result.scalars().all()

        return {review.recommendation_id: review for review in existing_reviews}

    def get_review_stats(self, session: Session, game_id: int) -> Dict[str, Any]:
        """Получить статистику отзывов для игры"""
        from sqlalchemy import func, Integer

        result = session.query(
            func.count(Review.id).label('total'),
            func.sum(func.cast(Review.voted_up, Integer)).label('positive'),
            func.sum(func.cast(~Review.voted_up, Integer)).label('negative'),
            func.avg(Review.weighted_vote_score).label('avg_score')
        ).filter(Review.game_id == game_id).first()

        return {
            'total_reviews': result.total or 0,
            'positive_reviews': result.positive or 0,
            'negative_reviews': result.negative or 0,
            'average_score': float(result.avg_score or 0)
        }