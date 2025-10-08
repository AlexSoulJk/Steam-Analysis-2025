from typing import List, Dict

from requests import Session

from steam_analysis.core.schemas.game.dictionaries import TypeCreate, TypeUpdate
from steam_analysis.database.models.game import GameType
from steam_analysis.database.repositories.base import DictionaryRepository


class TypeRepository(DictionaryRepository[GameType, TypeCreate, TypeUpdate]):

    def __init__(self):
        super().__init__(GameType)

    def bulk_get_or_create(self, items_data: List[TypeCreate], session: Session) -> Dict[str, GameType]:

        if not items_data:
            return {}

        # Получаем все имена для поиска

        descriptions = [item.description for item in items_data]
        descriptions = list(set(descriptions))
        # Ищем существующие записи
        existing_ids = self.get_by_steam_descriptions(descriptions, session=session)
        existing_map = {item.description: item for item in existing_ids}

        # Определяем какие нужно создать
        to_create = {}
        for item in items_data:
            if item.description not in existing_map:
                to_create[item.description] = item

        # Создаем новые записи
        if to_create:
            created_items = self.create_bulk(list(to_create.values()), session=session)
            for item in created_items:
                existing_map[item.description] = item

        return existing_map

    def get_by_steam_descriptions(self, steam_ids: List[str], session: Session) -> List[GameType]:
        """Получить записи по списку steam_id"""
        if not steam_ids:
            return []

        return session.query(self.model).filter(self.model.description.in_(steam_ids)).all()
