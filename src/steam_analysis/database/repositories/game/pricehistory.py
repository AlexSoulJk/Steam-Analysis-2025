# repositories/price_history_repository.py
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, or_, desc, asc
from datetime import datetime, date

from ..base.base import BaseDBRepository
from ...models import PriceHistory, Game
from steam_analysis.core.schemas.game.pricehistory import (
    PriceHistoryCreate, PriceHistoryBase
)


class PriceHistoryRepository(BaseDBRepository[PriceHistory, PriceHistoryCreate, Any]):
    """Репозиторий для работы с историей цен игр"""

    def __init__(self):
        super().__init__(model=PriceHistory)

    def get_by_game_id(self, session: Session, game_id: int,
                       skip: int = 0, limit: int = 100) -> List[PriceHistory]:
        """Получить историю цен для конкретной игры"""
        query = select(self.model). \
            where(self.model.game_id == game_id). \
            order_by(desc(self.model.created_at)). \
            offset(skip).limit(limit)

        result = session.execute(query)
        return list(result.scalars().all())

    def get_by_game_id_and_currency(self, session: Session, game_id: int,
                                    currency: str = 'USD') -> List[PriceHistory]:
        """Получить историю цен для игры в конкретной валюте"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.currency == currency
            )
        ). \
            order_by(desc(self.model.created_at))

        result = session.execute(query)
        return list(result.scalars().all())

    def get_latest_price(self, session: Session, game_id: int,
                         currency: str = 'USD') -> Optional[PriceHistory]:
        """Получить последнюю запись цены для игры"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.currency == currency
            )
        ). \
            order_by(desc(self.model.created_at)). \
            limit(1)

        result = session.execute(query)
        return result.scalar_one_or_none()

    def get_price_at_date(self, session: Session, game_id: int,
                          target_date: date, currency: str = 'USD') -> Optional[PriceHistory]:
        """Получить цену игры на конкретную дату (ближайшую к дате)"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.currency == currency,
                self.model.created_at.cast(date) <= target_date
            )
        ). \
            order_by(desc(self.model.created_at)). \
            limit(1)

        result = session.execute(query)
        return result.scalar_one_or_none()

    def get_price_range(self, session: Session, game_id: int,
                        start_date: date, end_date: date,
                        currency: str = 'USD') -> List[PriceHistory]:
        """Получить историю цен за период"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.currency == currency,
                self.model.created_at.cast(date) >= start_date,
                self.model.created_at.cast(date) <= end_date
            )
        ). \
            order_by(asc(self.model.created_at))

        result = session.execute(query)
        return list(result.scalars().all())

    def get_games_with_discounts(self, session: Session,
                                 min_discount: int = 10,
                                 currency: str = 'USD',
                                 skip: int = 0, limit: int = 100) -> List[Tuple[Game, PriceHistory]]:
        """Получить игры со скидками выше указанного процента"""
        from sqlalchemy import func

        # Получаем последние цены для каждой игры
        subquery = session.query(
            PriceHistory.game_id,
            func.max(PriceHistory.created_at).label('latest_date')
        ). \
            filter(
            PriceHistory.currency == currency,
            PriceHistory.discount_percent >= min_discount
        ). \
            group_by(PriceHistory.game_id). \
            subquery()

        query = session.query(Game, PriceHistory). \
            join(PriceHistory, Game.id == PriceHistory.game_id). \
            join(
            subquery,
            and_(
                PriceHistory.game_id == subquery.c.game_id,
                PriceHistory.created_at == subquery.c.latest_date
            )
        ). \
            offset(skip).limit(limit)

        return query.all()

    def get_historical_low(self, session: Session, game_id: int,
                           currency: str = 'USD') -> Optional[PriceHistory]:
        """Получить исторический минимум цены для игры"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.currency == currency
            )
        ). \
            order_by(asc(self.model.price_final)). \
            limit(1)

        result = session.execute(query)
        return result.scalar_one_or_none()

    def get_historical_high(self, session: Session, game_id: int,
                            currency: str = 'USD') -> Optional[PriceHistory]:
        """Получить исторический максимум цены для игры"""
        query = select(self.model). \
            where(
            and_(
                self.model.game_id == game_id,
                self.model.currency == currency
            )
        ). \
            order_by(desc(self.model.price_final)). \
            limit(1)

        result = session.execute(query)
        return result.scalar_one_or_none()

    def create_bulk(self, session: Session,
                    price_histories: List[PriceHistoryCreate]) -> List[PriceHistory]:
        """
        Массовое создание записей истории цен

        Note: Для истории цен обычно не проверяем на дубликаты,
        так как цена может быть одинаковой в разные даты
        """
        if not price_histories:
            return []

        db_objects = []
        for price_data in price_histories:
            # Рассчитываем initial если не передан
            if hasattr(price_data, 'initial'):
                initial = price_data.initial
            else:
                # Рассчитываем initial из final и discount
                if price_data.discount_percent > 0:
                    initial = int(price_data.price_final / (1 - price_data.discount_percent / 100))
                else:
                    initial = price_data.price_final

            db_obj = PriceHistory(
                game_id=price_data.game_id,
                currency=price_data.currency,
                price_final=price_data.price_final,
                price_initial=initial,
                discount_percent=price_data.discount_percent
            )
            db_objects.append(db_obj)

        session.add_all(db_objects)
        # session.commit()

        # for db_obj in db_objects:
        #     session.refresh(db_obj)

        return db_objects

    def create_from_base_schema(self, session: Session,
                                game_id: int,
                                price_data: PriceHistoryBase) -> PriceHistory:
        """Создать запись цены из базовой схемы"""
        # Рассчитываем initial
        if hasattr(price_data, 'initial'):
            initial = price_data.initial
        else:
            if price_data.discount_percent > 0:
                initial = int(price_data.price_final / (1 - price_data.discount_percent / 100))
            else:
                initial = price_data.price_final

        price_history = PriceHistory(
            game_id=game_id,
            currency=price_data.currency,
            price_final=price_data.price_final,
            price_initial=initial,
            discount_percent=price_data.discount_percent
        )

        session.add(price_history)
        # session.commit()
        # session.refresh(price_history)

        return price_history

    def get_games_price_changes(self, session: Session,
                                game_ids: List[int],
                                currency: str = 'USD') -> Dict[int, Dict[str, Any]]:
        """Получить изменения цен для списка игр"""
        from sqlalchemy import func

        if not game_ids:
            return {}

        # Получаем первые и последние записи для каждой игры
        first_prices = {}
        last_prices = {}

        for game_id in game_ids:
            # Первая запись
            first_query = select(self.model). \
                where(
                and_(
                    self.model.game_id == game_id,
                    self.model.currency == currency
                )
            ). \
                order_by(asc(self.model.created_at)). \
                limit(1)

            first_result = session.execute(first_query).scalar_one_or_none()
            if first_result:
                first_prices[game_id] = first_result

            # Последняя запись
            last_query = select(self.model). \
                where(
                and_(
                    self.model.game_id == game_id,
                    self.model.currency == currency
                )
            ). \
                order_by(desc(self.model.created_at)). \
                limit(1)

            last_result = session.execute(last_query).scalar_one_or_none()
            if last_result:
                last_prices[game_id] = last_result

        # Формируем результат
        result = {}
        for game_id in game_ids:
            first_price = first_prices.get(game_id)
            last_price = last_prices.get(game_id)

            if not first_price or not last_price:
                continue

            price_change = last_price.price_final - first_price.price_final
            if first_price.price_final > 0:
                percent_change = (price_change / first_price.price_final) * 100
            else:
                percent_change = 0.0

            result[game_id] = {
                'first_price': first_price.price_final,
                'last_price': last_price.price_final,
                'price_change': price_change,
                'percent_change': round(percent_change, 2),
                'first_date': first_price.created_at,
                'last_date': last_price.created_at,
                'current_discount': last_price.discount_percent
            }

        return result
