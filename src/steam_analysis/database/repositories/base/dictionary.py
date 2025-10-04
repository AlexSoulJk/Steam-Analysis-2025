from typing import Optional, Dict
from steam_analysis.database.repositories.base.base import ModelType, CreateSchemaType, UpdateSchemaType, \
    BaseDBRepository


class DictionaryRepository(BaseDBRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Репозиторий для справочников с дополнительными методами"""

    def get_by_name(self, name: str) -> Optional[ModelType]:
        return self.get_by_field("description", name)

    def get_or_create_by_name(self, name: str, defaults: Optional[Dict] = None) -> ModelType:
        """Получить или создать запись по имени"""
        db_obj = self.get_by_name(name)
        if db_obj:
            return db_obj

        create_data = {"description": name}
        if defaults:
            create_data.update(defaults)

        return self.create(self.create_schema_type(**create_data))
