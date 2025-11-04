import json
import os
from pathlib import Path
from typing import Optional, List

from .base import Resource, logger
from .codes import ResourceCodes
from ...core.schemas import PlayerShortInfo

#  переписать под юзера
class UserList(Resource):
    """Ресурс для хранения списка приложений Steam"""

    def __init__(self, resource_base_path: Path):
        super().__init__(ResourceCodes.USER_LIST,
                         resource_base_path=resource_base_path,
                         ttl_hours=72)

    def get_steam_id_list(self, steam_id_start: int, size: int) -> Optional[List[PlayerShortInfo]]:
        if not self.data:
            return None
        # count = 0
        # start_index = list(filter(lambda x, count: x['appid'] == app_id_start, count += 1, self.data))[0]['appid']
        start_index = next(i for i, item in enumerate(self.data) if item['steam_id'] == steam_id_start)
        end_index = min(len(self.data), start_index + size)
        return list(map(lambda x: x['steam_id'], self.data[start_index:end_index]))

    def get_app_list(self, steam_id_start: int, size: int) -> Optional[List[PlayerShortInfo]]:
        if not self.data:
            return None
        # count = 0
        # start_index = list(filter(lambda x, count: x['appid'] == app_id_start, count += 1, self.data))[0]['appid']
        start_index = next(i for i, item in enumerate(self.data) if item['steam_id'] == steam_id_start)
        end_index = min(len(self.data), start_index + size)
        return list(map(lambda x: PlayerShortInfo(steam_id=x["steam_id"], persona_name=x["persona_name"]), self.data[start_index:end_index]))

    def get_first_steam_id(self):
        if not self.data:
            return None
        return self.data[0]['steam_id']

    def load(self) -> bool:
        """Загрузить данные из файла"""
        try:
            if not os.path.exists(self.file_path):
                return False

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.update(data.get("data"), data.get("last_upd"))
                self._is_loaded = True
                return True

        except Exception as e:
            logger.error(f"Failed to load resource {self.name}: {e}")
            self._is_loaded = False
            return False

    def save(self) -> bool:
        """Сохранить данные в файл"""
        if self._data is None:
            return False

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({"last_upd": self._last_updated, "data": self._data}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save resource {self.name}: {e}")
            return False
