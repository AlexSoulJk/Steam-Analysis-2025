from typing import Optional, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas.game.service import SchemaCreate
from steam_analysis.core.schemas.game.dictionaries import AchievCreateDB, AchievUpdate
from steam_analysis.database.models.game import Achievement
from steam_analysis.database.repositories.base import DictionaryRepository
from .game import GameRepository

from steam_analysis.database.repositories.base.base import ModelType, CreateSchemaType, UpdateSchemaType, \
    BaseDBRepository


class AchievRepository(DictionaryRepository[Achievement, AchievCreateDB, AchievUpdate]):

    def __init__(self):
        super().__init__(Achievement)
        self.game_repos = GameRepository()

    def get_existing_by_game_names(self, game_id: int, names: List[str], session: Session) -> Dict[str, Achievement]:
        """
        Получить существующие достижения для конкретной игры по списку names
        Возвращает словарь {name: achievement_object}
        """
        if not names:
            return {}

        stmt = select(self.model).where(
            self.model.game_id == game_id,
            self.model.name.in_(names)
        )
        result = session.execute(stmt)
        existing_achievements = result.scalars().all()

        return {achievement.name: achievement for achievement in existing_achievements}

    def create_bulk(self, objects_in: List[AchievCreateDB], session: Session) -> List[Achievement]:
        """
        Массовое создание достижений

        Args:
            objects_in: Список объектов AchievCreateDB
            session: Сессия SQLAlchemy

        Returns:
            Список созданных и существующих достижений
        """
        if not objects_in:
            return []

        # Шаг 1: Группируем достижения по game_id
        achievements_by_game: Dict[int, List[AchievCreateDB]] = {}

        for achiev in objects_in:
            game_id = achiev.game_id
            if game_id not in achievements_by_game:
                achievements_by_game[game_id] = []
            achievements_by_game[game_id].append(achiev)

        # Шаг 2: Получаем существующие достижения для каждой игры
        all_achievements: List[Achievement] = []
        new_db_objects: List[Achievement] = []

        for game_id, achievements in achievements_by_game.items():
            # Получаем имена всех достижений для этой игры
            names = [achiev.name for achiev in achievements]

            # Получаем существующие достижения
            existing_achievements = self.get_existing_by_game_names(game_id, names, session)

            # Фильтруем новые достижения
            new_achievements = [
                achiev for achiev in achievements
                if achiev.name not in existing_achievements
            ]

            # Добавляем существующие достижения в общий список
            all_achievements.extend(existing_achievements.values())

            if not new_achievements:
                continue

            # Шаг 3: Создаем новые достижения
            for achiev_data in new_achievements:
                try:
                    # Преобразуем Pydantic модель в словарь
                    if hasattr(achiev_data, 'model_dump'):
                        obj_data = achiev_data.model_dump()
                    else:
                        obj_data = achiev_data.dict()

                    db_obj = self.model(
                        game_id=game_id,
                        name=obj_data.get('name', ''),
                        display_name=obj_data.get('displayName', ''),
                        hidden=bool(obj_data.get('hidden', 0))
                    )
                    new_db_objects.append(db_obj)

                except Exception as e:
                    print(f"Ошибка при создании достижения {achiev_data.name} для игры {game_id}: {e}")
                    continue

        if not new_db_objects:
            return all_achievements

        session.add_all(new_db_objects)

        all_achievements.extend(new_db_objects)

        return all_achievements



