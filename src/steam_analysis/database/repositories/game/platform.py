from typing import List, Dict

from requests import Session

from steam_analysis.core.schemas.game.dictionaries import PlatformCreate, PlatformUpdate
from steam_analysis.database.models.game import Platform
from steam_analysis.database.repositories.base import DictionaryRepository



class PlatformRepository(DictionaryRepository[Platform, PlatformCreate, PlatformUpdate]):

    def __init__(self):
        super().__init__(Platform)

    def bulk_get_or_create(self, items_data: List[PlatformCreate], session: Session) -> Dict[str, Platform]:
        pass
