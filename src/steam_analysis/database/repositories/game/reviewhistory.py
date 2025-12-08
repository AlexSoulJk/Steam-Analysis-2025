# repositories/review_history_repository.py
from typing import Optional, List, Dict, Tuple, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, or_, desc, asc, func, between
from datetime import datetime, date, timedelta

from ..base.base import BaseDBRepository
from ...models import ReviewHistory, Game
from steam_analysis.core.schemas.game.reviewhistory import (
    ReviewHistoryCreate,
    ReviewHistoryUpdate
)


class ReviewHistoryRepository(BaseDBRepository[ReviewHistory, ReviewHistoryCreate, ReviewHistoryUpdate]):
    """Репозиторий для работы с историей отзывов игр"""

    def __init__(self):
        super().__init__(model=ReviewHistory)

    def get_by_game_id(self, session: Session, game_id: int,
                       skip: int = 0, limit: int = 100,
                       order_by: str = 'newest') -> List[ReviewHistory]:
        """Получить историю отзывов для конкретной игры"""
        query = select(self.model).where(self.model.game_id == game_id)

        # Сортировка
        if order_by == 'newest':
            query = query.order_by(desc(self.model.created_at))
        elif order_by == 'oldest':
            query = query.order_by(asc(self.model.created_at))
        elif order_by == 'score_desc':
            query = query.order_by(desc(self.model.review_score))
        elif order_by == 'score_asc':
            query = query.order_by(asc(self.model.review_score))

        query = query.offset(skip).limit(limit)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_latest_by_game_id(self, session: Session, game_id: int) -> Optional[ReviewHistory]:
        """Получить последнюю запись истории отзывов для игры"""
        query = select(self.model). \
            where(self.model.game_id == game_id). \
            order_by(desc(self.model.created_at)). \
            limit(1)

        result = session.execute(query)
        return result.scalar_one_or_none()

    def get_by_date_range(self, session: Session, game_id: int,
                          start_date: date, end_date: date) -> List[ReviewHistory]:
        """Получить историю отзывов за период"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.created_at >= start_date,
                self.model.created_at <= end_date
            )
        ). \
            order_by(asc(self.model.created_at))

        result = session.execute(query)
        return list(result.scalars().all())

    def get_at_date(self, session: Session, game_id: int,
                    target_date: date) -> Optional[ReviewHistory]:
        """Получить запись истории отзывов на конкретную дату (ближайшую)"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                func.date(self.model.created_at) <= target_date
            )
        ). \
            order_by(desc(self.model.created_at)). \
            limit(1)

        result = session.execute(query)
        return result.scalar_one_or_none()

    def get_games_latest_reviews(self, session: Session,
                                 game_ids: List[int]) -> Dict[int, ReviewHistory]:
        """Получить последние записи истории отзывов для списка игр"""
        if not game_ids:
            return {}

        # Создаем подзапрос для получения последней записи для каждой игры
        subquery = session.query(
            ReviewHistory.game_id,
            func.max(ReviewHistory.created_at).label('max_date')
        ). \
            filter(ReviewHistory.game_id.in_(game_ids)). \
            group_by(ReviewHistory.game_id). \
            subquery()

        query = session.query(ReviewHistory). \
            join(
            subquery,
            and_(
                ReviewHistory.game_id == subquery.c.game_id,
                ReviewHistory.created_at == subquery.c.max_date
            )
        )

        latest_reviews = query.all()

        return {review.game_id: review for review in latest_reviews}

    def get_trend_data(self, session: Session, game_id: int,
                       days: int = 30) -> Dict[str, Any]:
        """Получить данные о тренде отзывов за период"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Получаем первую и последнюю записи за период
        first_record = session.query(ReviewHistory). \
            filter(
            ReviewHistory.game_id == game_id,
            ReviewHistory.created_at >= start_date
        ). \
            order_by(asc(ReviewHistory.created_at)). \
            first()

        last_record = session.query(ReviewHistory). \
            filter(
            ReviewHistory.game_id == game_id,
            ReviewHistory.created_at >= start_date
        ). \
            order_by(desc(ReviewHistory.created_at)). \
            first()

        if not first_record or not last_record:
            return {
                'trend': 'no_data',
                'score_change': 0.0,
                'review_count_change': 0,
                'positive_change': 0,
                'negative_change': 0
            }

        # Рассчитываем изменения
        score_change = last_record.review_score - first_record.review_score
        review_count_change = last_record.review_count - first_record.review_count
        positive_change = last_record.positive_reviews - first_record.positive_reviews
        negative_change = last_record.negative_reviews - first_record.negative_reviews

        # Определяем тренд
        if score_change > 0.01:
            trend = 'improving'
        elif score_change < -0.01:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'first_record': {
                'score': first_record.review_score,
                'total': first_record.review_count,
                'positive': first_record.positive_reviews,
                'negative': first_record.negative_reviews,
                'date': first_record.created_at
            },
            'last_record': {
                'score': last_record.review_score,
                'total': last_record.review_count,
                'positive': last_record.positive_reviews,
                'negative': last_record.negative_reviews,
                'date': last_record.created_at
            },
            'changes': {
                'score': score_change,
                'total': review_count_change,
                'positive': positive_change,
                'negative': negative_change
            },
            'period_days': days
        }

    def get_top_games_by_score(self, session: Session,
                               min_reviews: int = 100,
                               limit: int = 20) -> List[Tuple[Game, ReviewHistory]]:
        """Получить топ игр по оценке отзывов"""
        # Создаем подзапрос для получения последней записи для каждой игры
        subquery = session.query(
            ReviewHistory.game_id,
            func.max(ReviewHistory.created_at).label('max_date')
        ). \
            group_by(ReviewHistory.game_id). \
            subquery()

        query = session.query(Game, ReviewHistory). \
            join(ReviewHistory, Game.id == ReviewHistory.game_id). \
            join(
            subquery,
            and_(
                ReviewHistory.game_id == subquery.c.game_id,
                ReviewHistory.created_at == subquery.c.max_date
            )
        ). \
            filter(
            ReviewHistory.review_count >= min_reviews,
            ReviewHistory.review_score.isnot(None)
        ). \
            order_by(desc(ReviewHistory.review_score)). \
            limit(limit)

        return query.all()

    def get_most_improved_games(self, session: Session,
                                days: int = 30,
                                min_reviews: int = 50,
                                limit: int = 20) -> List[Dict[str, Any]]:
        """Получить игры с наибольшим улучшением отзывов за период"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Получаем первую запись для каждой игры за период
        first_records_subq = session.query(
            ReviewHistory.game_id,
            func.min(ReviewHistory.created_at).label('first_date')
        ). \
            filter(ReviewHistory.created_at >= start_date). \
            group_by(ReviewHistory.game_id). \
            subquery()

        # Получаем последнюю запись для каждой игры за период
        last_records_subq = session.query(
            ReviewHistory.game_id,
            func.max(ReviewHistory.created_at).label('last_date')
        ). \
            filter(ReviewHistory.created_at >= start_date). \
            group_by(ReviewHistory.game_id). \
            subquery()

        # Получаем данные первой записи
        first_records_data = session.query(
            ReviewHistory.game_id,
            ReviewHistory.review_score.label('first_score'),
            ReviewHistory.review_count.label('first_total')
        ). \
            join(
            first_records_subq,
            and_(
                ReviewHistory.game_id == first_records_subq.c.game_id,
                ReviewHistory.created_at == first_records_subq.c.first_date
            )
        ). \
            filter(ReviewHistory.review_count >= min_reviews). \
            subquery()

        # Получаем данные последней записи
        last_records_data = session.query(
            ReviewHistory.game_id,
            ReviewHistory.review_score.label('last_score'),
            ReviewHistory.review_count.label('last_total')
        ). \
            join(
            last_records_subq,
            and_(
                ReviewHistory.game_id == last_records_subq.c.game_id,
                ReviewHistory.created_at == last_records_subq.c.last_date
            )
        ). \
            subquery()

        # Объединяем данные и вычисляем улучшение
        query = session.query(
            Game,
            first_records_data.c.first_score,
            last_records_data.c.last_score,
            (last_records_data.c.last_score - first_records_data.c.first_score).label('improvement'),
            first_records_data.c.first_total,
            last_records_data.c.last_total
        ). \
            join(first_records_data, Game.id == first_records_data.c.game_id). \
            join(last_records_data, Game.id == last_records_data.c.game_id). \
            filter(
            last_records_data.c.last_score > first_records_data.c.first_score,  # Только улучшения
            last_records_data.c.last_total >= min_reviews
        ). \
            order_by(desc('improvement')). \
            limit(limit)

        results = query.all()

        return [
            {
                'game': game,
                'first_score': first_score,
                'last_score': last_score,
                'improvement': improvement,
                'improvement_percent': (improvement / first_score * 100) if first_score > 0 else 0,
                'first_total': first_total,
                'last_total': last_total,
                'review_growth': last_total - first_total
            }
            for game, first_score, last_score, improvement, first_total, last_total in results
        ]

    def get_most_declined_games(self, session: Session,
                                days: int = 30,
                                min_reviews: int = 50,
                                limit: int = 20) -> List[Dict[str, Any]]:
        """Получить игры с наибольшим ухудшением отзывов за период"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Аналогично get_most_improved_games, но фильтруем по ухудшению
        first_records_subq = session.query(
            ReviewHistory.game_id,
            func.min(ReviewHistory.created_at).label('first_date')
        ). \
            filter(ReviewHistory.created_at >= start_date). \
            group_by(ReviewHistory.game_id). \
            subquery()

        last_records_subq = session.query(
            ReviewHistory.game_id,
            func.max(ReviewHistory.created_at).label('last_date')
        ). \
            filter(ReviewHistory.created_at >= start_date). \
            group_by(ReviewHistory.game_id). \
            subquery()

        first_records_data = session.query(
            ReviewHistory.game_id,
            ReviewHistory.review_score.label('first_score'),
            ReviewHistory.review_count.label('first_total')
        ). \
            join(
            first_records_subq,
            and_(
                ReviewHistory.game_id == first_records_subq.c.game_id,
                ReviewHistory.created_at == first_records_subq.c.first_date
            )
        ). \
            filter(ReviewHistory.review_count >= min_reviews). \
            subquery()

        last_records_data = session.query(
            ReviewHistory.game_id,
            ReviewHistory.review_score.label('last_score'),
            ReviewHistory.review_count.label('last_total')
        ). \
            join(
            last_records_subq,
            and_(
                ReviewHistory.game_id == last_records_subq.c.game_id,
                ReviewHistory.created_at == last_records_subq.c.last_date
            )
        ). \
            subquery()

        query = session.query(
            Game,
            first_records_data.c.first_score,
            last_records_data.c.last_score,
            (last_records_data.c.last_score - first_records_data.c.first_score).label('decline'),
            first_records_data.c.first_total,
            last_records_data.c.last_total
        ). \
            join(first_records_data, Game.id == first_records_data.c.game_id). \
            join(last_records_data, Game.id == last_records_data.c.game_id). \
            filter(
            last_records_data.c.last_score < first_records_data.c.first_score,  # Только ухудшения
            last_records_data.c.last_total >= min_reviews
        ). \
            order_by(asc('decline')). \
            limit(limit)

        results = query.all()

        return [
            {
                'game': game,
                'first_score': first_score,
                'last_score': last_score,
                'decline': abs(decline),
                'decline_percent': (abs(decline) / first_score * 100) if first_score > 0 else 0,
                'first_total': first_total,
                'last_total': last_total
            }
            for game, first_score, last_score, decline, first_total, last_total in results
        ]

    def get_daily_summary(self, session: Session,
                          target_date: date) -> Dict[str, Any]:
        """Получить суммарную статистику отзывов за день"""
        # Получаем записи за день
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        query = session.query(
            func.count(ReviewHistory.id).label('total_entries'),
            func.sum(ReviewHistory.review_count).label('total_reviews'),
            func.avg(ReviewHistory.review_score).label('avg_score'),
            func.sum(ReviewHistory.positive_reviews).label('total_positive'),
            func.sum(ReviewHistory.negative_reviews).label('total_negative')
        ). \
            filter(
            ReviewHistory.created_at >= start_datetime,
            ReviewHistory.created_at <= end_datetime
        )

        result = query.first()

        if not result or not result.total_entries:
            return {
                'date': target_date,
                'total_entries': 0,
                'total_reviews': 0,
                'avg_score': 0.0,
                'total_positive': 0,
                'total_negative': 0,
                'positive_ratio': 0.0
            }

        total_reviews = result.total_reviews or 0
        total_positive = result.total_positive or 0

        return {
            'date': target_date,
            'total_entries': result.total_entries,
            'total_reviews': total_reviews,
            'avg_score': float(result.avg_score or 0),
            'total_positive': total_positive,
            'total_negative': result.total_negative or 0,
            'positive_ratio': (total_positive / total_reviews * 100) if total_reviews > 0 else 0.0
        }

    def create_bulk(self, session: Session,
                    review_histories: List[ReviewHistoryCreate]) -> List[ReviewHistory]:
        """
        Массовое создание записей истории отзывов
        """
        if not review_histories:
            return []

        db_objects = []
        for history_data in review_histories:
            db_obj = ReviewHistory(
                game_id=history_data.game_id,
                review_score=history_data.review_score,
                review_count=history_data.review_count,
                positive_reviews=history_data.positive_reviews,
                negative_reviews=history_data.negative_reviews
            )
            db_objects.append(db_obj)

        session.add_all(db_objects)
        # session.commit()

        # for db_obj in db_objects:
        #     session.refresh(db_obj)

        return db_objects

