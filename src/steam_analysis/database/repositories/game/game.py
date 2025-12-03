from collections import defaultdict
from typing import Optional, List, Dict, Tuple

from sqlalchemy import select, func, extract, Integer
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas import GameCreate, GameUpdate
from steam_analysis.proccessors.schemas.games import GamesByCountCategoriesWithSubs, GamesReleaseBySeason

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