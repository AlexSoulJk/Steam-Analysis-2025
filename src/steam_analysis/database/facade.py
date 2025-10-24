import os
from operator import or_
from typing import Dict, List

from steam_analysis.config import db_path
from steam_analysis.core.schemas.game.service import FillGameAnalysisChunk, GameDataAnalysisCreate
from steam_analysis.core.services.schema_morpher import SchemaMorpher
from steam_analysis.database.models import Game, GameGenre, GameCategory, GamePlatform
from steam_analysis.database.repositories import GameRepository
from contextlib import contextmanager
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session

from steam_analysis.database.repositories.game.category import CategoryRepository
from steam_analysis.database.repositories.game.genre import GenreRepository
from steam_analysis.database.repositories.game.platform import PlatformRepository
from steam_analysis.database.repositories.game.type import TypeRepository
from steam_analysis.database.support_models.game_creation import PreparedForGameCreation

# Для Windows абсолютного пути:
engine = create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    """Простой контекстный менеджер"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Или еще проще:
def get_db_session():
    """Просто возвращает сессию (нужно закрывать вручную)"""
    return SessionLocal()


class DbFacade:

    def __init__(self):
        self.game_repos = GameRepository()
        self.categories = CategoryRepository()
        self.types = TypeRepository()
        self.platforms = PlatformRepository()
        self.genres = GenreRepository()
        # self.price = PriceHistory()

    def _prepare_data_for_game_creation(self,
                                        data_without_none: list[GameDataAnalysisCreate]) -> PreparedForGameCreation:
        types = list(map(lambda x: x.game.type, data_without_none))
        with get_db() as session:
            platforms = self.platforms.bulk_get_or_create(list(map(lambda x: x.platforms, data_without_none)),
                                                          session=session)
            genres = self.genres.bulk_get_or_create(list(map(lambda x: x.genres, data_without_none)), session=session)
            categories = self.categories.bulk_get_or_create(list(map(lambda x: x.categories, data_without_none)),
                                                            session=session)
            types = self.types.bulk_get_or_create(types, session=session)

        return PreparedForGameCreation(categories=categories,
                                       genres=genres,
                                       types=types,
                                       platforms=platforms)

    def _prepare_relations(self, games, dict_without_none, prep_info):
        """Подготавливает все связи для создания"""
        game_genres = []
        game_categories = []
        game_platforms = []

        for game in games:
            data = dict_without_none[game.app_id]

            for genre_create in data.genres:
                genre = prep_info.genres[genre_create.steam_id]
                game_genres.append(GameGenre(game_id=game.id, genre_id=genre.id))

            for category_create in data.categories:
                category = prep_info.categories[category_create.steam_id]
                game_categories.append(GameCategory(game_id=game.id, category_id=category.id))

            for platform_create in data.platforms:
                platform = prep_info.platforms[platform_create.description]
                game_platforms.append(GamePlatform(game_id=game.id, platform_id=platform.id))

        return game_genres, game_categories, game_platforms

    def _create_connections(self, prep_info: PreparedForGameCreation,
                            games: List[Game], dict_without_none: Dict[int, GameDataAnalysisCreate],
                            session: Session):
        # 1. Подготавливаем все связи
        game_genres, game_categories, game_platforms = self._prepare_relations(
            games, dict_without_none, prep_info
        )

        # 2. Проверяем существующие связи одним запросом для каждого типа
        unique_game_genres = self._filter_existing_relations(
            session, GameGenre, game_genres, ['game_id', 'genre_id']
        )
        unique_game_categories = self._filter_existing_relations(
            session, GameCategory, game_categories, ['game_id', 'category_id']
        )
        unique_game_platforms = self._filter_existing_relations(
            session, GamePlatform, game_platforms, ['game_id', 'platform_id']
        )

        # 3. Создаем только уникальные связи
        session.add_all(unique_game_genres + unique_game_categories + unique_game_platforms)
        session.commit()

    def _filter_existing_relations(self, session, model, relations, unique_fields):
        """Фильтрует существующие связи массово - улучшенная версия"""
        if not relations:
            return []

        # Создаем списки значений для каждого поля
        field_values = {field: [] for field in unique_fields}
        for relation in relations:
            for field in unique_fields:
                field_values[field].append(getattr(relation, field))

        # Создаем условие с in_() для каждого поля
        conditions = []
        for field in unique_fields:
            if field_values[field]:
                conditions.append(getattr(model, field).in_(field_values[field]))

        if not conditions:
            return relations

        # Объединяем условия через AND (все поля должны совпадать)
        combined_condition = and_(*conditions)

        # Ищем существующие связи
        existing_relations = session.query(model).filter(combined_condition).all()
        existing_set = set(
            tuple(getattr(rel, field) for field in unique_fields)
            for rel in existing_relations
        )

        # Фильтруем только новые связи
        unique_relations = [
            relation for relation in relations
            if tuple(getattr(relation, field) for field in unique_fields) not in existing_set
        ]

        return unique_relations

    def create_games(self, games_info_chunk: FillGameAnalysisChunk):
        data_without_none = list(filter(lambda x: x is not None, games_info_chunk.data_chunk))

        prep_info = self._prepare_data_for_game_creation(data_without_none=data_without_none)
        games_to_create = SchemaMorpher.game_create_from_http_to_database(
            games=list(map(lambda x: x.game, data_without_none)),
            types=prep_info.types)

        with get_db() as session:
            games = self.game_repos.create_bulk(games_to_create, session=session)
            dict_without_nons = {data_analys_schema.game.app_id: data_analys_schema for data_analys_schema in data_without_none}
            self._create_connections(prep_info=prep_info, dict_without_none=dict_without_nons,
                                     games=games, session=session)

    def get_last_upploaded_game(self):
        with get_db() as session:
            return self.game_repos.get_last_uploaded_game(session=session)

    # region Gets Row data for simple-visualisation
    def get_games_by_categories(self):
        pass

    def get_games_by_genres(self):
        pass

    # endregion

