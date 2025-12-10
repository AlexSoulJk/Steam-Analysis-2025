from typing import List, Any
from sqlalchemy.orm import Session
from steam_analysis.core.schemas.game.dictionaries import AchievPercentCreateDB
from steam_analysis.database.models.timeseries import AchievementHistory
from steam_analysis.database.repositories.base.base import BaseDBRepository

class AchievementHistoryRepository(BaseDBRepository[AchievementHistory, AchievPercentCreateDB, Any]):
    """Репозиторий для работы с историей изменения статистики достижений."""

    def __init__(self):
        super().__init__(AchievementHistory)
        # Опционально: размер батча для очень больших пачек данных
        self._insert_batch_size = 1000

    def create_bulk(self, objects_in: List[AchievPercentCreateDB], session: Session) -> List[AchievementHistory]:
        """
        Массовое создание записей истории достижений (логирование данных).
        Каждый объект в списке создаёт новую запись в таблице, даже если для
        данного achievement_id записи уже существуют.

        Args:
            objects_in: Список объектов с данными нового замера.
            session: Сессия SQLAlchemy.

        Returns:
            Список созданных объектов ORM (опционально).
        """
        if not objects_in:
            return []

        db_objects = []
        for obj_in in objects_in:
            try:
                if hasattr(obj_in, 'model_dump'):
                    obj_data = obj_in.model_dump()
                else:
                    obj_data = obj_in.dict()

                db_obj = self.model(
                    achievement_id=obj_data['achievement_id'],
                    global_achievement_rate=obj_data['percent']  # Маппинг здесь
                )
                db_objects.append(db_obj)

            except Exception as e:
                print(f"Ошибка создания записи истории для achievement_id={obj_in.achievement_id}: {e}")
                continue

        session.add_all(db_objects)

        return db_objects