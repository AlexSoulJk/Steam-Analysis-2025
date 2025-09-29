import json
import os
from pathlib import Path

from .base import Resource, logger
from .codes import ResourceCodes


class GameList(Resource):
    """Ресурс для хранения списка приложений Steam"""

    def __init__(self, resource_base_path: Path):
        super().__init__(ResourceCodes.GAME_LIST,
                         resource_base_path=resource_base_path,
                         ttl_hours=24)

    def load(self) -> bool:
        """Загрузить данные из файла"""
        try:
            if not os.path.exists(self.file_path):
                return False

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.update(data)
                return True

        except Exception as e:
            logger.error(f"Failed to load resource {self.name}: {e}")
            return False

    def save(self) -> bool:
        """Сохранить данные в файл"""
        if self._data is None:
            return False

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save resource {self.name}: {e}")
            return False
