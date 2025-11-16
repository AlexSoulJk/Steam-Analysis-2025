from typing import Optional, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from steam_analysis.core.schemas.game.service import SchemaCreate
from steam_analysis.core.schemas.game.dictionaries import AchievCreate, AchievUpdate
from steam_analysis.database.models.game import Achievement
from steam_analysis.database.repositories.base import DictionaryRepository
from steam_analysis.database.repositories import GameRepository

from steam_analysis.database.repositories.base.base import ModelType, CreateSchemaType, UpdateSchemaType, \
    BaseDBRepository


class AchievRepository(DictionaryRepository[Achievement, AchievCreate, AchievUpdate]):

    def __init__(self):
        super().__init__(Achievement)
        self.game_repos = GameRepository()

    def create_bulk(self, objects_in: List[SchemaCreate], session: Session) -> List[Achievement]:
        """
        Массовое создание объектов

        Args:
            objects_in: Список Pydantic схем

        Returns:
            Список созданных объектов
        """

        created_achievements = []

        app_ids = list(objects_in.keys())
        existing_games_map = self.game_repos.get_existing_by_app_ids(app_ids, session)

        for schema in objects_in.values():
            # Проверяем, существует ли игра
            if schema.game_id not in existing_games_map:
                print(f"Игра с app_id {schema.game_id} не найдена в базе")
                continue

            for achiev_data in schema.achievs:
                try:
                    # Проверяем, существует ли уже такое достижение
                    existing_achievement = session.query(Achievement).filter(
                        Achievement.game_id == schema.game_id,
                        Achievement.name == achiev_data.name
                    ).first()
                    
                    if existing_achievement:
                        print(f"Достижение {achiev_data.name} для игры {schema.game_id} уже существует")
                        continue

                    # Создаем новое достижение
                    achievement = Achievement(
                        game_id=schema.game_id,
                        name=achiev_data.name,
                        display_name=achiev_data.display_name,
                        # description=None,
                        # icon_url=achiev_data.icon,
                        # icon_gray_url=achiev_data.icon_gray,
                        # achieved=False,
                        # unlock_time=None,
                        # global_achievement_rate=0.0,
                        # api_name=achiev_data.name,
                        hidden=bool(achiev_data.hidden)
                    )
                    
                    session.add(achievement)
                    created_achievements.append(achievement)
                    
                except Exception as e:
                    print(f"Ошибка при создании достижения {achiev_data.name}: {e}")
                    continue
        try:
            session.commit()
            # Обновляем объекты, чтобы получить их с ID
            for achievement in created_achievements:
                session.refresh(achievement)
            return created_achievements
        
        except Exception as e:
            print(f"Ошибка при коммите: {e}")
            session.rollback()
            return []



