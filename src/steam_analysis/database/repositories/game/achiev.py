from typing import Optional, Dict, List, Tuple

from sqlalchemy import select, and_, or_
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

        result_dict: Dict[str, Achievement] = {}

        # Разбиваем names на батчи
        for i in range(0, len(names), 500):
            batch = names[i:i + 500]

            stmt = select(self.model).where(
                self.model.game_id == game_id,
                self.model.name.in_(batch) if len(batch) > 1 else self.model.name == batch[0]
            )
            result = session.execute(stmt)
            batch_achievements = result.scalars().all()

            # Добавляем в общий словарь
            for achievement in batch_achievements:
                result_dict[achievement.name] = achievement

        return result_dict

    def get_existing_pairs(self, session: Session, pairs: List[Tuple[int, str]],
                           batch_size: int = 500) -> List[Achievement]:
        """
        Получить существующие достижения по парам (game_id, name) с батчингом

        Args:
            session: Сессия SQLAlchemy
            pairs: Список кортежей (game_id, name)
            batch_size: Размер батча (если None, используется self._batch_size)

        Returns:
            Список существующих достижений
        """
        if not pairs:
            return []

        all_existing = []

        # Обрабатываем пары батчами
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]

            # Создаем OR-условия для текущего батча
            conditions = []
            for game_id, name in batch:
                conditions.append(
                    and_(
                        self.model.game_id == game_id,
                        self.model.name == name
                    )
                )

            # Выполняем запрос для текущего батча
            if conditions:
                stmt = select(self.model).where(or_(*conditions))
                result = session.execute(stmt)
                batch_existing = list(result.scalars().all())
                all_existing.extend(batch_existing)

        return all_existing

    def create_bulk(self, schemas: List[AchievCreateDB], session: Session) -> List[Achievement]:
        """
        Массовое создание достижений с проверкой по парам

        Args:
            session: Сессия SQLAlchemy
            schemas: Список Pydantic схем AchievCreateDB
            query_batch_size: Размер батча для проверки существующих
            insert_batch_size: Размер батча для вставки новых

        Returns:
            Список созданных и существующих достижений
        """
        if not schemas:
            return []

        pairs = [(schema.game_id, schema.name) for schema in schemas]

        existing_achievements = self.get_existing_pairs(session, pairs)

        existing_pairs_set = {
            (achievement.game_id, achievement.name) for achievement in existing_achievements
        }

        new_schemas = []
        for schema in schemas:
            pair_key = (schema.game_id, schema.name)
            if pair_key not in existing_pairs_set:
                new_schemas.append(schema)

        if not new_schemas:
            return existing_achievements

        new_achievements = []
        for schema in new_schemas:
            try:
                # Преобразуем схему в словарь
                if hasattr(schema, 'model_dump'):
                    obj_data = schema.model_dump()
                else:
                    obj_data = schema.dict()

                # Создаем объект ORM
                achievement = Achievement(
                    game_id=schema.game_id,
                    name=obj_data.get('name', ''),
                    display_name=obj_data.get('displayName', ''),
                    hidden=bool(obj_data.get('hidden', 0))
                )
                new_achievements.append(achievement)

            except Exception as e:
                print(f"Ошибка при создании достижения {schema.name} для игры {schema.game_id}: {e}")
                continue

        if not new_achievements:
            return existing_achievements

        session.add_all(new_achievements)

        # Шаг 4: Возвращаем все достижения (существующие + новые)
        return existing_achievements + new_achievements

