from typing import Optional, Dict, List

from sqlalchemy.orm import Session

from steam_analysis.database.repositories.base.base import ModelType, CreateSchemaType, UpdateSchemaType, \
    BaseDBRepository


class DictionaryRepository(BaseDBRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Репозиторий для справочников с дополнительными методами"""

    def bulk_get_or_create(self, items_data: List[List[CreateSchemaType]], session: Session) -> Dict[str, ModelType]:
        """
        Массовое получение или создание записей справочника.
        Возвращает словарь {name: db_object} для быстрого доступа.
        """
        if not items_data:
            return {}

        # Получаем все имена для поиска

        steam_ids = [item.steam_id for items in items_data for item in items]
        steam_ids = list(set(steam_ids))
        # Ищем существующие записи
        existing_ids = self.get_by_steam_ids(steam_ids, session=session)
        existing_map = {item.item: item for item in existing_ids}

        # Определяем какие нужно создать
        to_create = []
        for item_data in items_data:
            if item_data.steam_id not in existing_map:
                to_create.append(item_data)

        # Создаем новые записи
        if to_create:
            created_items = self.create_bulk(to_create, session=session)
            for item in created_items:
                existing_map[item.id] = item

        return existing_map

    def get_by_name(self, name: str, session: Session) -> Optional[ModelType]:
        return self.get_by_field("description", name, session=session)

    def get_by_steam_ids(self, steam_ids: List[int], session: Session) -> List[ModelType]:
        """Получить записи по списку steam_id"""
        if not steam_ids:
            return []

        return session.query(self.model).filter(self.model.id.in_(steam_ids)).all()

    def get_or_create_by_name(self, session: Session, name: str, defaults: Optional[Dict] = None) -> ModelType:
        """Получить или создать запись по имени"""
        db_obj = self.get_by_name(name, session)
        if db_obj:
            return db_obj

        create_data = {"description": name}
        if defaults:
            create_data.update(defaults)

        return self.create(self.create_schema_type(**create_data), session=session)
