from typing import List, Dict

from requests import Session

from steam_analysis.core.schemas.game.dictionaries import PlatformCreate, PlatformUpdate
from steam_analysis.database.models.game import Platform
from steam_analysis.database.repositories.base import DictionaryRepository


class PlatformRepository(DictionaryRepository[Platform, PlatformCreate, PlatformUpdate]):

    def __init__(self):
        super().__init__(Platform)

    def bulk_get_or_create(self, items_data: List[List[PlatformCreate]], session: Session) -> Dict[str, Platform]:
        if not items_data:
            return {}

        # Получаем все имена для поиска

        descriptions = [item.description for items in items_data for item in items]
        descriptions = list(set(descriptions))
        # Ищем существующие записи
        existing_ids = self.get_by_steam_descriptions(descriptions, session=session)
        existing_map = {item.description: item for item in existing_ids}

        # Определяем какие нужно создать
        to_create = {}
        for items in items_data:
            for item_data in items:
                if item_data.description not in existing_map:
                    to_create[item_data.description] = item_data

        # Создаем новые записи
        if to_create:
            created_items = self.create_bulk(list(to_create.values()), session=session)
            for item in created_items:
                existing_map[item.description] = item

        return existing_map

    def get_by_steam_descriptions(self, steam_ids: List[str], session: Session) -> List[Platform]:
        """Получить записи по списку steam_id"""
        if not steam_ids:
            return []

        return session.query(self.model).filter(self.model.description.in_(steam_ids)).all()
