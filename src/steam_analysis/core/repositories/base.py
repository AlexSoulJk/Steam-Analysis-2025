from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]: ...

    # @abstractmethod
    # def get_all(self, filters: dict = None) -> List[Dict[str, Any]]: ...