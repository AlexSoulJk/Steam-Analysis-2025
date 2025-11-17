from typing import List, Dict

from sqlalchemy import and_
from sqlalchemy.orm import Session

from steam_analysis.core.schemas.game.service import UserDataAnalysisCreate
from steam_analysis.database.models import GameGenre, GamePlatform, GameCategory, Game
from steam_analysis.database.support_models.game_creation import PreparedForGameCreation


class GameRelationsCreationService:

    def __init__(self):
        pass

    def _prepare_relations(self, games,
                           dict_without_none,
                           prep_info):

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

        return game_genres, \
            game_categories, \
            game_platforms

    def create_connections(self, prep_info: PreparedForGameCreation,
                           games: List[Game],
                           dict_without_none: Dict[int, UserDataAnalysisCreate],
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
