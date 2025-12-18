from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from steam_analysis.resourcemanager.manager import resource_manager


class BaseRepository(ABC):

    def __init__(self):
        self.resource_manager = resource_manager
    @abstractmethod
    def get_by_id(self, id: int | str, **kwargs) -> Optional[Any]: ...

    @abstractmethod
    def get_by_ids(self, ids: list[int] | list[str], **kwargs) -> Optional[List[Any]]: ...
    # @abstractmethod
    # def get_all(self, filters: dict = None) -> List[Dict[str, Any]]: ...