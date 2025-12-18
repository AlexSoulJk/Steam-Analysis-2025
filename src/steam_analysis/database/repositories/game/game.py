from collections import defaultdict
from typing import Optional, List, Dict, Tuple,  Any

from sqlalchemy import func, extract, case, and_, or_, distinct
from sqlalchemy import select, func, extract, Integer
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas import GameCreate, GameUpdate
from steam_analysis.proccessors.schemas.games import (AbstractGameBy_, GamesClusteringData,
                                                      TwoDHistogramData, GamesReleaseBySeason,
                                                      EnhancedHistogramData, GameFeatureVector,
                                                      GamesByTypes, GamesByCategories, GamesByCountCategoriesWithSubs, \
                                                      GamesByGenres, CharacterByPrice)

from ..base.base import BaseDBRepository
from ...models import Game
from ...models.game import GameGenre, GameCategory, GamePlatform, GameMetrics, Achievement, Category, Genre
from ...models.timeseries import PriceHistory, ReviewHistory, PlayerCountHistory

from datetime import datetime


EXCHANGE_RATES = {
            'USD': 92.5, 'EUR': 100.0, 'GBP': 117.0, 'RUB': 1.0,
            'JPY': 0.62, 'CNY': 12.8, 'CAD': 67.5, 'CHF': 106.0,
            'SGD': 68.0, 'HKD': 11.8, 'NOK': 8.4, 'PLN': 23.0,
            'BRL': 18.5, 'MXN': 5.4, 'INR': 1.1, 'KRW': 0.069,
            'THB': 2.6, 'IDR': 0.0059, 'MYR': 19.5, 'PHP': 1.65,
            'VND': 0.0038, 'ZAR': 5.0, 'SAR': 24.7, 'CLP': 0.105,
            'COP': 0.023, 'CRC': 0.17, 'KWD': 300.0, 'NZD': 55.0,
            'TWD': 2.9, 'UYU': 2.4, 'AED': 21.69, 'AUD': 53.03,
            'DEFAULT': 95.0
        }


def convert_to_rubles(amount: float, currency: str) -> float:
    if not amount or amount <= 0:
        return 0.0
    currency_code = currency.upper().strip() if currency else 'USD'
    rate = EXCHANGE_RATES.get(currency_code)
    if rate is None:
        rate = EXCHANGE_RATES.get('USD', 95.0)
    amount_in_units = amount / 100.0
    return amount_in_units * rate


class GameRepository(BaseDBRepository[Game, GameCreate, GameUpdate]):
    """Репозиторий для работы с играми"""

    def __init__(self):
        super().__init__(model=Game)

    def get_by_app_id(self, app_id: int, session: Session) -> Optional[Game]:
        return self.get_by_field("app_id",
                                 app_id,
                                 session=session)

    def get_existing_by_app_ids(self, app_ids: List[int], session: Session, batch_size: int = 500) -> Dict[int, Game]:
        """
        Получить существующие игры по списку app_ids одним запросом
        Возвращает словарь {app_id: game_object}
        """
        if not app_ids:
            return {}

        result_dict = {}

        # Обрабатываем батчи
        for i in range(0, len(app_ids), batch_size):
            batch = app_ids[i:i + batch_size]
            query = select(self.model).where(self.model.app_id.in_(batch))
            result = session.execute(query)
            existing_games = result.scalars().all()

            result_dict.update({game.app_id: game for game in existing_games})

        return result_dict


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

    def count_games_by_genres_for_type(
            self,
            session: Session,
            type_id: int = 1
    ) -> List[Tuple[str, int]]:
        from ...models.game import Genre, GameGenre

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


        # Используем базовый метод
        results = self.count_with_join_group_by(
            session=session,
            join_model=GameGenre,  # Первый JOIN
            join_condition=Game.id == GameGenre.game_id,
            group_by_field='genre_id',  # Группируем по названию категории
            count_field='id',
            filters={'type_id': type_id},
            additional_joins=[
            # Второй JOIN: GameCategory → Category
            (Genre, GameGenre.category_id == Genre.id)
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

    def get_games_ids(self, session: Session, start_id: int = None, limit: int = None):
        query = session.query(Game.app_id, Game.id)

        # Фильтр по начальному ID
        if start_id is not None:
            query = query.filter(Game.id >= start_id)

        # Ограничение количества
        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def get_games_by_category_combinations(
            self,
            session: Session,
            type_id: int = 1,
            max_category_count: int = 10
    ) -> GamesByCountCategoriesWithSubs:
        from ...models.game import Category, GameCategory
        """
        Получить игры по комбинациям категорий

        Args:
            session: SQLAlchemy сессия
            type_id: ID типа игр
            max_category_count: Максимальное количество категорий для анализа

        Returns:
            GamesByCountCategoriesWithSubs
        """

        # Шаг 1: Получаем все игры нужного типа с их категориями
        games_with_categories = session.execute(
            select(
                Game.id,
                Category.description
            )
            .join(GameCategory, Game.id == GameCategory.game_id)
            .join(Category, GameCategory.category_id == Category.id)
            .where(Game.type_id == type_id)
            .order_by(Game.id, Category.description)
        ).all()

        # Шаг 2: Группируем категории по играм
        game_categories = defaultdict(list)
        for game_id, category_desc in games_with_categories:
            game_categories[game_id].append(category_desc)

        # Шаг 3: Считаем комбинации для каждого количества категорий
        result = GamesByCountCategoriesWithSubs()
        result.values = defaultdict(lambda: defaultdict(int))
        result.ticks = list(range(1, max_category_count + 1))

        for game_id, categories in game_categories.items():
            category_count = len(categories)

            # Если количество категорий превышает максимум - пропускаем
            if category_count > max_category_count:
                continue

            # Создаем ключ комбинации (сортируем для единообразия)
            sorted_categories = sorted(categories)
            combination_key = ", ".join(sorted_categories)

            # Увеличиваем счетчик для этой комбинации
            result.values[category_count][combination_key] += 1

        # Убираем пустые категории
        result.values = {k: dict(v) for k, v in result.values.items() if v}

        return result

    def get_games_by_category_combinations_sql(
            self,
            session: Session,
            type_id: int = 1,
            max_category_count: int = 10
    ) -> GamesByCountCategoriesWithSubs:
        """
        Тот же результат, но чисто через SQL (быстрее для больших данных)
        """
        from ...models.game import Category, GameCategory

        values = {}
        ticks = list(range(1, max_category_count + 1))

        # Для каждого количества категорий делаем отдельный запрос
        for category_count in range(1, max_category_count + 1):
            # CTE: получаем игры с нужным количеством категорий
            games_with_n_categories = (
                select(GameCategory.game_id)
                .group_by(GameCategory.game_id)
                .having(func.count(GameCategory.category_id) == category_count)
                .cte('games_n_categories')
            )

            # Основной запрос: для этих игр собираем комбинации категорий
            query = (
                select(
                    func.group_concat(Category.description, ', ').label('combination'),
                    func.count('*').label('game_count')
                )
                .select_from(GameCategory)
                .join(Category, GameCategory.category_id == Category.id)
                .join(games_with_n_categories,
                      GameCategory.game_id == games_with_n_categories.c.game_id)
                .join(Game, Game.id == games_with_n_categories.c.game_id)
                .where(Game.type_id == type_id)
                .group_by(GameCategory.game_id)  # Группируем по игре чтобы получить комбинацию
                .subquery()
            )

            # Теперь группируем по комбинациям
            final_query = (
                select(
                    query.c.combination,
                    func.count('*').label('total_games')
                )
                .select_from(query)
                .group_by(query.c.combination)
                .order_by(func.count('*').desc())
            )

            combos = session.execute(final_query).all()

            if combos:
                values[category_count] = {
                    combo: count for combo, count in combos
                }

        return GamesByCountCategoriesWithSubs(values=values,
                                              ticks=ticks)

    def get_top_combinations_per_count(
            self,
            session: Session,
            type_id: int = 1,
            top_n: int = 5,
            max_category_count: int = 10
    ) -> Dict[int, List[Tuple[str, int]]]:
        """
        Получить топ-N комбинаций для каждого количества категорий
        (упрощенная версия для отладки)
        """
        from ...models.game import Category, GameCategory

        result = {}

        for category_count in range(1, max_category_count + 1):
            # Простой запрос для каждой группы
            query = (
                select(
                    func.group_concat(Category.description, ', ').label('combination'),
                    func.count('*').label('game_count')
                )
                .select_from(Game)
                .join(GameCategory, Game.id == GameCategory.game_id)
                .join(Category, GameCategory.category_id == Category.id)
                .where(Game.type_id == type_id)
                .group_by(Game.id)
                .having(func.count(Category.id) == category_count)
                .subquery()
            )

            final_query = (
                select(
                    query.c.combination,
                    func.count('*').label('total')
                )
                .select_from(query)
                .group_by(query.c.combination)
                .order_by(func.count('*').desc())
                .limit(top_n)
            )

            combos = session.execute(final_query).all()

            if combos:
                result[category_count] = combos

        return result

    def get_games_release_by_season(
            self,
            session: Session,
            season_mode: str = "monthly",
            year: Optional[int] = None,
            type_id: int = 1
    , ):
        """
        Получить распределение релизов по сезонам (месяцам или кварталам)

        Args:
            session: SQLAlchemy сессия
            season_mode: 'monthly' (по месяцам) или 'quarter' (по кварталам)
            year: Фильтр по году (опционально)
            type_id: Фильтр по типу игры (опционально)

        Returns:
            GamesReleaseBySeason с распределением по сезонам
        """

        if season_mode == "monthly":
            # 0-11 для месяцев (январь=1, но в SQLite extract выдаст 1-12)
            ticks = list(range(1, 13))
            season_expr = extract('month', Game.release_date)
        elif season_mode == "quarter":
            # 1-4 для кварталов
            ticks = list(range(1, 5))
            # Квартал = ceil(месяц / 3)
            season_expr = func.cast((extract('month', Game.release_date) + 2) / 3, Integer)
        else:
            raise ValueError(f"Unknown season_mode: {season_mode}")

        # Базовый запрос
        query = select(
            season_expr.label('season'),
            func.count(Game.id).label('count')
        ).where(
            Game.release_date.isnot(None)
        )

        # Применяем фильтры
        if year:
            query = query.where(extract('year', Game.release_date) == year)

        if type_id:
            query = query.where(Game.type_id == type_id)

        # Группировка и сортировка
        query = query.group_by(season_expr).order_by(season_expr)

        # Выполняем запрос
        db_result = session.execute(query).all()

        # Преобразуем в словарь, заполняя нулями отсутствующие сезоны
        values = {}
        for tick in ticks:
            values[tick] = 0

        for season, count in db_result:
            # SQLite может вернуть месяц как 1.0 (float)
            season_int = int(season)
            if season_int in values:
                values[season_int] = count

        return values, ticks

    def get_prices_by_category(self,
                               session: Session,
                               n: int = 10,
                               price_type: str = 'final',
                               min_games: int = 1,
                               convert_to_rub: bool = True,
                               type_id: int = 1) -> CharacterByPrice:
        """
        Получает распределение цен по топ-N категориям с учетом валюты

        Args:
            session: SQLAlchemy сессия
            n: количество топ категорий
            price_type: 'final' или 'initial' цена
            min_games: минимальное количество игр в категории
            convert_to_rub: конвертировать ли в рубли
            type_id: ID типа игры (по умолчанию 1 - игры)
        """
        # Определяем поле цены в зависимости от типа
        price_field = getattr(PriceHistory, f'price_{price_type}')

        # 1. Сначала получаем топ-N категорий по количеству игр
        top_categories_subq = (
            select(
                Category.id.label('category_id'),
                Category.description.label('category_name'),
                func.count(distinct(Game.id)).label('games_count')
            )
            .select_from(Category)
            .join(GameCategory, GameCategory.category_id == Category.id)
            .join(Game, Game.id == GameCategory.game_id)
            .where(Game.is_free == False)
            .where(Game.type_id == type_id)  # ← ДОБАВЛЕНО!
            .group_by(Category.id, Category.description)
            .having(func.count(distinct(Game.id)) >= min_games)
            .order_by(func.count(distinct(Game.id)).desc())
            .limit(n)
            .subquery('top_categories')
        )

        # 2. Подзапрос для получения последней цены каждой игры
        latest_prices_subq = (
            select(
                PriceHistory.game_id,
                func.max(PriceHistory.created_at).label('latest_date')
            )
            .group_by(PriceHistory.game_id)
            .subquery('latest_prices')
        )

        # 3. Основной запрос
        query = (
            select(
                top_categories_subq.c.category_name,
                PriceHistory.currency,
                func.avg(price_field).label('avg_price'),
                top_categories_subq.c.games_count
            )
            .select_from(top_categories_subq)
            .join(GameCategory, GameCategory.category_id == top_categories_subq.c.category_id)
            .join(Game, Game.id == GameCategory.game_id)
            .join(latest_prices_subq, Game.id == latest_prices_subq.c.game_id)
            .join(
                PriceHistory,
                (PriceHistory.game_id == Game.id) &
                (PriceHistory.created_at == latest_prices_subq.c.latest_date)
            )
            .where(price_field.isnot(None))
            .where(price_field > 0)
            .where(Game.type_id == type_id)  # ← ДОБАВЛЕНО здесь тоже!
            .group_by(
                top_categories_subq.c.category_id,
                top_categories_subq.c.category_name,
                PriceHistory.currency,
                top_categories_subq.c.games_count
            )
            .order_by(func.count(distinct(Game.id)).desc())
        )

        result = session.execute(query).all()

        print(f"Результатов запроса для type_id={type_id}: {len(result)}")

        # Формируем данные для схемы
        values = []
        ticks = []
        currency_stats = {}

        for row in result:
            if row.avg_price:
                label = f"{row.category_name}"
                ticks.append(label)

                price_value = float(row.avg_price)

                # Конвертируем в рубли
                if convert_to_rub and row.currency:
                    price_converted = convert_to_rubles(price_value, row.currency)
                    currency_stats[row.currency] = currency_stats.get(row.currency, 0) + 1
                else:
                    # Если не конвертируем, просто переводим центы в базовые единицы
                    price_converted = price_value / 100.0  # Предполагаем центы

                values.append(price_converted)

                # Отладочный вывод для первых 5 записей
                if len(values) <= 5:
                    print(f"  Категория: {row.category_name}, "
                          f"Цена исходная: {price_value:.2f}, "
                          f"Валюта: {row.currency}, "
                          f"Цена результат: {price_converted:.2f}")
        if currency_stats:
            print(f"Статистика валют: {currency_stats}")
        if len(ticks) > n:
            ticks = ticks[:n]
            values = values[:n]
        try:
            return CharacterByPrice(values=values, ticks=ticks)
        except Exception as e:
            print(f"Ошибка при создании CharacterByPrice: {e}")
            # Фоллбэк
            return {"values": values, "ticks": ticks}


    def get_prices_by_genre(self,
                            session: Session,
                            n: int = 10,
                            price_type: str = 'final',
                            min_games: int = 1,
                            convert_to_rub: bool = True) -> CharacterByPrice:
        """
        Получает распределение цен по топ-N жанрам с учетом валюты
        """
        price_field = getattr(PriceHistory, f'price_{price_type}')

        top_genres_subq = (
            select(
                Genre.id.label('genre_id'),
                Genre.description.label('genre_name'),
                func.count(distinct(Game.id)).label('games_count')
            )
            .select_from(Genre)
            .join(GameGenre, GameGenre.genre_id == Genre.id)
            .join(Game, Game.id == GameGenre.game_id)
            .where(Game.is_free == False)
            .group_by(Genre.id, Genre.description)
            .having(func.count(distinct(Game.id)) >= min_games)
            .order_by(func.count(distinct(Game.id)).desc())
            .limit(n)
            .subquery('top_genres')
        )

        latest_prices_subq = (
            select(
                PriceHistory.game_id,
                func.max(PriceHistory.created_at).label('latest_date')
            )
            .group_by(PriceHistory.game_id)
            .subquery('latest_prices')
        )

        query = (
            select(
                top_genres_subq.c.genre_name,
                PriceHistory.currency,  # Включаем валюту
                func.avg(price_field).label('avg_price'),
                top_genres_subq.c.games_count
            )
            .select_from(top_genres_subq)
            .join(GameGenre, GameGenre.genre_id == top_genres_subq.c.genre_id)
            .join(Game, Game.id == GameGenre.game_id)
            .join(latest_prices_subq, Game.id == latest_prices_subq.c.game_id)
            .join(
                PriceHistory,
                (PriceHistory.game_id == Game.id) &
                (PriceHistory.created_at == latest_prices_subq.c.latest_date)
            )
            .where(price_field.isnot(None))
            .where(price_field > 0)
            .group_by(
                top_genres_subq.c.genre_id,
                top_genres_subq.c.genre_name,
                PriceHistory.currency,  # Группируем по валюте
                top_genres_subq.c.games_count
            )
            .order_by(func.avg(price_field).desc())
        )

        result = session.execute(query).all()

        values = []
        ticks = []
        currency_stats = {}

        for row in result:
            if row.avg_price:
                label = f"{row.genre_name}"
                ticks.append(label)

                price_value = float(row.avg_price)

                price_value = convert_to_rubles(price_value, row.currency)
                currency_stats[row.currency] = currency_stats.get(row.currency, 0) + 1

                values.append(price_value)

        if currency_stats:
            print(f"Валюты по жанрам: {currency_stats}")

        return CharacterByPrice(values=values, ticks=ticks)

    def get_game_clustering_data(
            self,
            session: Session,
            type_id: int = 1,
            limit: Optional[int] = None,
            min_review_count: int = 5
    ) -> GamesClusteringData:

        game_query = (
            select(
                Game.id,
                Game.app_id,
                Game.name,
                Game.is_free,
                Game.release_date,
            )
            .where(Game.type_id == type_id)
            .where(Game.release_date.isnot(None))
        )

        if limit:
            game_query = game_query.limit(limit)

        try:
            game_results = session.execute(game_query).all()
        except Exception as e:
            print(f"Ошибка выполнения запроса игр: {e}")
            return GamesClusteringData(
                games=[],
                feature_names=[],
                feature_matrix=None,
                values={"total_games": 0, "feature_count": 0, "type_id": type_id},
                ticks=[]
            )

        if not game_results:
            print("Нет игр в базе")
            return GamesClusteringData(
                games=[],
                feature_names=[],
                feature_matrix=None,
                values={"total_games": 0, "feature_count": 0, "type_id": type_id},
                ticks=[]
            )

        print(f"Найдено {len(game_results)} игр")
        game_ids = [row[0] for row in game_results]

        latest_prices = {}
        batch_size = 100

        for i in range(0, len(game_ids), batch_size):
            batch_ids = game_ids[i:i + batch_size]
            try:
                prices_subquery = (
                    select(
                        PriceHistory.game_id,
                        PriceHistory.currency,
                        PriceHistory.price_final,
                        PriceHistory.price_initial,
                        func.row_number().over(
                            partition_by=PriceHistory.game_id,
                            order_by=PriceHistory.created_at.desc()
                        ).label('row_num')
                    )
                    .where(PriceHistory.game_id.in_(batch_ids))
                    .subquery()
                )

                prices_query = (
                    select(
                        prices_subquery.c.game_id,
                        prices_subquery.c.currency,
                        prices_subquery.c.price_final,
                        prices_subquery.c.price_initial
                    )
                    .where(prices_subquery.c.row_num == 1)
                )

                prices_result = session.execute(prices_query).all()
                for row in prices_result:
                    game_id, currency, price_final, price_initial = row
                    price_amount = None
                    if price_final is not None:
                        price_amount = price_final
                    elif price_initial is not None:
                        price_amount = price_initial

                    if price_amount is not None:
                        price_rub = convert_to_rubles(float(price_amount), currency)
                        MAX_PRICE_RUB = 10000.0
                        if price_rub > MAX_PRICE_RUB:
                            price_rub = MAX_PRICE_RUB
                        latest_prices[game_id] = price_rub

                if i % 500 == 0:
                    print(f"  Обработано цен для {i} игр...")

            except Exception as e:
                print(f"Ошибка запроса цен для батча {i}: {e}")
                continue

        print(f"  Получено цен для {len(latest_prices)} игр")
        latest_reviews = {}

        for i in range(0, len(game_ids), batch_size):
            batch_ids = game_ids[i:i + batch_size]
            try:
                reviews_subquery = (
                    select(
                        ReviewHistory.game_id,
                        ReviewHistory.review_score,
                        ReviewHistory.review_count,
                        func.row_number().over(
                            partition_by=ReviewHistory.game_id,
                            order_by=ReviewHistory.created_at.desc()
                        ).label('row_num')
                    )
                    .where(ReviewHistory.game_id.in_(batch_ids))
                    .subquery()
                )

                reviews_query = (
                    select(
                        reviews_subquery.c.game_id,
                        reviews_subquery.c.review_score,
                        reviews_subquery.c.review_count
                    )
                    .where(reviews_subquery.c.row_num == 1)
                )

                reviews_result = session.execute(reviews_query).all()
                for row in reviews_result:
                    game_id, review_score, review_count = row
                    latest_reviews[game_id] = {
                        'review_score': review_score,
                        'review_count': review_count
                    }
                if i % 500 == 0:
                    print(f"  Обработано отзывов для {i} игр...")
            except Exception as e:
                print(f"Ошибка запроса отзывов для батча {i}: {e}")
                continue
        print(f"  Получено отзывов для {len(latest_reviews)} игр")
        achievements_dict = {}
        for i in range(0, len(game_ids), batch_size):
            batch_ids = game_ids[i:i + batch_size]
            try:
                achievements_query = (
                    select(
                        Achievement.game_id,
                        func.count(Achievement.id).label("achievements_count")
                    )
                    .where(Achievement.game_id.in_(batch_ids))
                    .group_by(Achievement.game_id)
                )
                achievements_result = session.execute(achievements_query).all()
                for row in achievements_result:
                    achievements_dict[row[0]] = row[1]

                if i % 500 == 0:
                    print(f"  Обработано достижений для {i} игр...")

            except Exception as e:
                print(f"Ошибка запроса достижений для батча {i}: {e}")
                continue

        print(f"  Получено достижений для {len(achievements_dict)} игр")

        game_vectors = []
        feature_matrix = []
        feature_names = [
            "price_rub",  # Цена в рублях (основной финансовый показатель)
            "is_free",  # Бесплатная ли игра (бинарный)
            "review_score",  # Общий рейтинг (0-1) - главный показатель качества
            "review_confidence",  # Уверенность в рейтинге (log10(отзывов+1))
            "review_count_log",  # Логарифм количества отзывов (популярность)
            "achievements_count_norm",  # Количество достижений (нормализованное)
            "game_age_years",  # Возраст игры в годах
            # "release_month_sin",  # Синус месяца релиза (сезонность)
            # "release_month_cos",  # Косинус месяца релиза (сезонность)
        ]

        current_year = datetime.now().year
        processed_count = 0
        games_with_price = 0
        games_with_reviews = 0
        skipped_low_reviews = 0

        import math

        print(f"\nНачинаю обработку {len(game_results)} игр...")
        for row in game_results:
            try:
                game_id, app_id, name, is_free, release_date = row
                features = {}
                features["is_free"] = 1.0 if is_free else 0.0

                price_rub = 0.0
                if is_free:
                    price_rub = 0.0
                elif game_id in latest_prices:
                    price_rub = latest_prices[game_id]
                    if price_rub > 0:
                        games_with_price += 1
                features["price_rub"] = price_rub
                review_data = latest_reviews.get(game_id, {})
                review_score = review_data.get('review_score')
                review_count = review_data.get('review_count', 0)
                if min_review_count > 0 and review_count < min_review_count:
                    skipped_low_reviews += 1
                    continue

                if review_count and review_count > 0:
                    games_with_reviews += 1

                features["review_score"] = float(review_score or 0.0)
                features["review_confidence"] = math.log10(float(review_count or 0) + 1)
                features["review_count_log"] = math.log10(float(review_count or 0) + 1)
                achievements = float(achievements_dict.get(game_id, 0))
                features["achievements_count_norm"] = min(achievements / 1000.0, 1.0) if achievements > 0 else 0.0
                if release_date:
                    age = max(1, current_year - release_date.year)
                    month = release_date.month
                else:
                    age = 1.0
                    month = 1
                features["game_age_years"] = float(age)
                # month_rad = (month - 1) * (2 * math.pi / 12)  # Конвертируем в радианы
                # features["release_month_sin"] = math.sin(month_rad)
                # features["release_month_cos"] = math.cos(month_rad)

                feature_values = []
                for name_feature in feature_names:
                    value = features.get(name_feature, 0.0)
                    feature_values.append(float(value))

                game_vector = GameFeatureVector(
                    app_id=app_id,
                    name=name,
                    features=features,
                    feature_values=feature_values,
                    feature_names=feature_names.copy()
                )

                game_vectors.append(game_vector)
                feature_matrix.append(feature_values)
                processed_count += 1

                if processed_count % 100 == 0:
                    print(f"  Создано векторов для {processed_count} игр...")

            except Exception as e:
                print(f"Ошибка обработки игры {app_id if 'app_id' in locals() else 'Unknown'}: {e}")
                continue

        print(f"Обработано {len(game_vectors)} игр с метриками успешности")
        print(f"Игр с информацией о цене: {games_with_price}")
        print(f"Игр с отзывами (min_review_count={min_review_count}): {games_with_reviews}")
        if skipped_low_reviews > 0:
            print(f"Пропущено игр с малым количеством отзывов: {skipped_low_reviews}")

        if not game_vectors:
            print("Не удалось создать векторы")
            return GamesClusteringData(
                games=[],
                feature_names=[],
                feature_matrix=None,
                values={"total_games": 0, "feature_count": 0},
                ticks=[]
            )
        try:
            import numpy as np
            if feature_matrix:
                X = np.array(feature_matrix)
                print(f" Матрица признаков: {X.shape[0]} игр × {X.shape[1]} признаков")
                print("КЛЮЧЕВЫЕ ПРИЗНАКИ УСПЕШНОСТИ:")
                categories = {
                    "КАЧЕСТВО": ["review_score", "review_confidence"],
                    "ПОПУЛЯРНОСТЬ": ["review_count_log"],
                    "ФИНАНСЫ": ["price_rub", "is_free"],
                    "КОНТЕНТ": ["achievements_count_norm"],
                    "ВРЕМЯ": ["game_age_years", "release_month_sin", "release_month_cos"]
                }

                for category, features_list in categories.items():
                    print(f"\n{category}:")
                    for feature in features_list:
                        if feature in feature_names:
                            idx = feature_names.index(feature)
                            col = X[:, idx]
                            if feature.endswith('_log'):
                                print(f"   {feature:25} медиана={np.median(col):.2f}, std={col.std():.2f}")
                            elif feature == "price_rub":
                                non_zero = np.sum(col > 0)
                                if non_zero > 0:
                                    non_zero_values = col[col > 0]
                                    print(
                                        f"   {feature:25} ${np.median(non_zero_values):.0f} руб. ({non_zero} платных игр)")
                                else:
                                    print(f"   {feature:25} нет данных")
                            else:
                                print(
                                    f"   {feature:25} min={col.min():.3f}, med={np.median(col):.3f}, max={col.max():.3f}")
        except Exception as e:
            print(f"Ошибка анализа матрицы: {e}")

        stats = {
            "total_games": len(game_vectors),
            "feature_count": len(feature_names),
            "type_id": type_id,
            "min_review_count": min_review_count,
            "games_with_price": games_with_price,
            "games_with_reviews": games_with_reviews,
            "skipped_low_reviews": skipped_low_reviews,
            "feature_categories": {
                "quality": ["review_score", "review_confidence"],
                "popularity": ["review_count_log"],
                "financial": ["price_rub", "is_free"],
                "content": ["achievements_count_norm"],
                # "temporal": ["game_age_years", "release_month_sin", "release_month_cos"],
                "temporal": ["game_age_years"]
            }
        }

        return GamesClusteringData(
            games=game_vectors,
            feature_names=feature_names,
            feature_matrix=feature_matrix,
            values=stats,
            ticks=feature_names
        )

    def get_2d_hist_data(
            self,
            session: Session,
            x_field: str = "review_score",
            y_field: str = "price",
            type_id: int = 1,
            x_bins: int = 20,
            y_bins: int = 20,
            min_review_count: int = 10
    ) -> TwoDHistogramData:
        field_mapping = {
            "review_score": GameMetrics.review_score,
            "review_count": GameMetrics.review_count,
            "recommendations_count": GameMetrics.recommendations_count,
            "metacritic_score": GameMetrics.metacritic_score,
            "peak_players_all_time": GameMetrics.peak_players_all_time,
            "is_free": case((Game.is_free == True, 1), else_=0),
            "coming_soon": case((Game.coming_soon == True, 1), else_=0),
            "game_age_years": case(
                (Game.release_date.isnot(None),
                 datetime.now().year - extract('year', Game.release_date)),
                else_=0
            ),
            "price": (
                select(PriceHistory.price_final)
                .where(PriceHistory.game_id == Game.id)
                .order_by(PriceHistory.created_at.desc())
                .limit(1)
                .scalar_subquery()
            ),
            "achievements_count": (
                select(func.count(Achievement.id))
                .where(Achievement.game_id == Game.id)
                .scalar_subquery()
            ),
            "genres_count": (
                select(func.count(GameGenre.id))
                .where(GameGenre.game_id == Game.id)
                .scalar_subquery()
            ),
            "categories_count": (
                select(func.count(GameCategory.id))
                .where(GameCategory.game_id == Game.id)
                .scalar_subquery()
            )
        }
        if x_field not in field_mapping or y_field not in field_mapping:
            available_fields = list(field_mapping.keys())
            raise ValueError(
                f"Поле '{x_field}' или '{y_field}' не найдено. "
                f"Доступные поля: {', '.join(available_fields)}"
            )
        x_expr = field_mapping[x_field]
        y_expr = field_mapping[y_field]
        base_query = (
            select(Game)
            .join(GameMetrics, Game.id == GameMetrics.game_id, isouter=True)
            .where(Game.type_id == type_id)
            .where(or_(GameMetrics.review_count >= min_review_count,
                       GameMetrics.review_count == None))
        )
        games = session.execute(base_query).scalars().all()
        x_values = []
        y_values = []
        for game in games:
            try:
                if x_field == "price":
                    latest_price = session.execute(
                        select(PriceHistory.price_final)
                        .where(PriceHistory.game_id == game.id)
                        .order_by(PriceHistory.created_at.desc())
                        .limit(1)
                    ).scalar()
                    x_val = float(latest_price) if latest_price else 0.0
                elif x_field == "game_age_years":
                    if game.release_date:
                        x_val = datetime.now().year - game.release_date.year
                    else:
                        x_val = 0.0
                elif x_field in ["news_count", "achievements_count", "genres_count", "categories_count"]:
                    if x_field == "achievements_count":
                        count = session.execute(
                            select(func.count(Achievement.id))
                            .where(Achievement.game_id == game.id)
                        ).scalar() or 0
                    elif x_field == "genres_count":
                        count = session.execute(
                            select(func.count(GameGenre.id))
                            .where(GameGenre.game_id == game.id)
                        ).scalar() or 0
                    else:
                        count = session.execute(
                            select(func.count(GameCategory.id))
                            .where(GameCategory.game_id == game.id)
                        ).scalar() or 0
                    x_val = float(count)
                elif x_field == "is_free" or x_field == "coming_soon":
                    x_val = 1.0 if getattr(game, x_field) else 0.0
                elif game.metrics and hasattr(game.metrics, x_field):
                    val = getattr(game.metrics, x_field)
                    x_val = float(val) if val is not None else 0.0
                else:
                    x_val = 0.0
            except (ValueError, TypeError, AttributeError):
                x_val = 0.0
            try:
                if y_field == "price":
                    latest_price = session.execute(
                        select(PriceHistory.price_final)
                        .where(PriceHistory.game_id == game.id)
                        .order_by(PriceHistory.created_at.desc())
                        .limit(1)
                    ).scalar()
                    y_val = float(latest_price) if latest_price else 0.0
                elif y_field == "game_age_years":
                    if game.release_date:
                        y_val = datetime.now().year - game.release_date.year
                    else:
                        y_val = 0.0
                elif y_field in ["news_count", "achievements_count", "genres_count", "categories_count"]:
                    if y_field == "achievements_count":
                        count = session.execute(
                            select(func.count(Achievement.id))
                            .where(Achievement.game_id == game.id)
                        ).scalar() or 0
                    elif y_field == "genres_count":
                        count = session.execute(
                            select(func.count(GameGenre.id))
                            .where(GameGenre.game_id == game.id)
                        ).scalar() or 0
                    else:
                        count = session.execute(
                            select(func.count(GameCategory.id))
                            .where(GameCategory.game_id == game.id)
                        ).scalar() or 0
                    y_val = float(count)
                elif y_field == "is_free" or y_field == "coming_soon":
                    y_val = 1.0 if getattr(game, y_field) else 0.0
                elif game.metrics and hasattr(game.metrics, y_field):
                    val = getattr(game.metrics, y_field)
                    y_val = float(val) if val is not None else 0.0
                else:
                    y_val = 0.0
            except (ValueError, TypeError, AttributeError):
                y_val = 0.0

            if x_val is not None and y_val is not None:
                x_values.append(x_val)
                y_values.append(y_val)
        axis_labels = {
            "review_score": "Рейтинг (0-1)",
            "review_count": "Количество отзывов",
            "recommendations_count": "Количество рекомендаций",
            "metacritic_score": "Metacritic Score",
            "peak_players_all_time": "Пик игроков онлайн",
            "is_free": "Бесплатная игра",
            "coming_soon": "Скоро выйдет",
            "game_age_years": "Возраст игры (лет)",
            "price": "Цена ($)",
            "news_count": "Количество новостей",
            "achievements_count": "Количество достижений",
            "genres_count": "Количество жанров",
            "categories_count": "Количество категорий"
        }
        x_label = axis_labels.get(x_field, x_field)
        y_label = axis_labels.get(y_field, y_field)
        return TwoDHistogramData(
            x_values=x_values,
            y_values=y_values,
            x_bins=x_bins,
            y_bins=y_bins,
            x_label=x_label,
            y_label=y_label
        )

    def enhanced_histogram_data(
            self,
            session: Session,
            value_field: str = "review_score",
            type_id: int = 1,
            bins_method: str = "auto",
            min_review_count: int = 10,
            show_stats: bool = True,
            show_outliers: bool = True,
            compare_with_normal: bool = True,
            log_scale: bool = False,
            filter_free: Optional[bool] = None
    ) -> EnhancedHistogramData:
        field_configs = {
            "review_score": {
                "expr": GameMetrics.review_score,
                "name": "Рейтинг игры",
                "unit": "(0-1)",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "review_count": {
                "expr": GameMetrics.review_count,
                "name": "Количество отзывов",
                "unit": "",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "recommendations_count": {
                "expr": GameMetrics.recommendations_count,
                "name": "Количество рекомендаций",
                "unit": "",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "metacritic_score": {
                "expr": GameMetrics.metacritic_score,
                "name": "Metacritic Score",
                "unit": "(0-100)",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "peak_players_all_time": {
                "expr": GameMetrics.peak_players_all_time,
                "name": "Пик игроков онлайн",
                "unit": "игроков",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "game_age_years": {
                "expr": case(
                    (Game.release_date.isnot(None),
                     datetime.now().year - extract('year', Game.release_date)),
                    else_=0
                ),
                "name": "Возраст игры",
                "unit": "лет",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "price": {
                "expr": (
                    select(PriceHistory.price_final)
                    .where(PriceHistory.game_id == Game.id)
                    .order_by(PriceHistory.created_at.desc())
                    .limit(1)
                    .scalar_subquery()
                ),
                "name": "Цена игры",
                "unit": "$",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "achievements_count": {
                "expr": (
                    select(func.count(Achievement.id))
                    .where(Achievement.game_id == Game.id)
                    .scalar_subquery()
                ),
                "name": "Количество достижений",
                "unit": "",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "genres_count": {
                "expr": (
                    select(func.count(GameGenre.id))
                    .where(GameGenre.game_id == Game.id)
                    .scalar_subquery()
                ),
                "name": "Количество жанров",
                "unit": "",
                "transform": lambda x: float(x) if x is not None else 0.0
            },
            "categories_count": {
                "expr": (
                    select(func.count(GameCategory.id))
                    .where(GameCategory.game_id == Game.id)
                    .scalar_subquery()
                ),
                "name": "Количество категорий",
                "unit": "",
                "transform": lambda x: float(x) if x is not None else 0.0
            }
        }
        if value_field not in field_configs:
            available_fields = list(field_configs.keys())
            raise ValueError(
                f"Поле '{value_field}' не найдено. "
                f"Доступные поля: {', '.join(available_fields)}"
            )
        config = field_configs[value_field]
        query = (
            select(config["expr"].label('value'))
            .select_from(Game)
            .join(GameMetrics, Game.id == GameMetrics.game_id, isouter=True)
            .where(Game.type_id == type_id)
        )
        if min_review_count > 0:
            query = query.where(or_(
                GameMetrics.review_count >= min_review_count,
                GameMetrics.review_count == None
            ))
        if filter_free is not None:
            query = query.where(Game.is_free == filter_free)
        if value_field in ["review_score", "metacritic_score", "price"]:
            query = query.where(config["expr"] > 0)
        results = session.execute(query).all()
        values = []
        for row in results:
            if row.value is not None:
                try:
                    transformed_value = config["transform"](row.value)
                    values.append(transformed_value)
                except (ValueError, TypeError):
                    continue
        return EnhancedHistogramData(
            values=values,
            value_name=config["name"],
            unit=config["unit"],
            bins_method=bins_method,
            show_density=True,
            show_stats=show_stats,
            show_outliers=show_outliers,
            compare_with_normal=compare_with_normal,
            log_scale=log_scale,
            ticks=[]
        )
