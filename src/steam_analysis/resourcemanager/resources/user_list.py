import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import time

from .base import Resource, logger
from .codes import ResourceCodes
from ...core.schemas import PlayerShortInfo
from ...core.schemas.player.service import PlayerAnalysisForJson


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

    def get_current_steam_id_list(self):
        if not self.data:
            return None
        return list(map(lambda x: x['steam_id'], self.data))

    def get_last_unfilled_user(self):
        # TODO: Need add schema
        if not self.data:
            return None
        element = next(filter(lambda x: x['status'] == "unfilled", self.data), None)
        return element

    def get_app_list(self, steam_id_start: int, size: int) -> Optional[List[PlayerShortInfo]]:
        if not self.data:
            return None
        # count = 0
        # start_index = list(filter(lambda x, count: x['appid'] == app_id_start, count += 1, self.data))[0]['appid']
        start_index = next(i for i, item in enumerate(self.data) if item['steam_id'] == steam_id_start)
        end_index = min(len(self.data), start_index + size)
        return list(map(lambda x: PlayerShortInfo(steam_id=x["steam_id"], persona_name=x["persona_name"]),
                        self.data[start_index:end_index]))

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

    def _find_player_index(self, steam_id: str) -> int:
        """Находит индекс игрока по steam_id, возвращает -1 если не найден"""
        for i, player in enumerate(self.data):
            if player["steam_id"] == steam_id:
                return i
        return -1

    def _procces_from_request(self, requests):
        current_time = time.time()
        has_changes = False

        for new_player in requests:
            player_index = self._find_player_index(new_player.steam_id)

            if player_index == -1:
                # Новый игрок - добавляем
                player_data = new_player.dict()
                player_data["last_upd"] = current_time
                self.data.append(player_data)
                has_changes = True
                print(f"Добавлен новый игрок: {new_player.steam_id}")

            else:
                # Существующий игрок - проверяем можно ли обновлять
                existing_player = self.data[player_index]

                # Не обновляем если статус filled или close_f_list
                if existing_player["status"] in ["filled", "close_f_list"]:
                    print(
                        f"Игрок {new_player.steam_id} имеет статус {existing_player['status']} - пропускаем обновление")
                    continue

                # Проверяем, есть ли реальные изменения
                needs_update = (
                        existing_player["persona_name"] != new_player.persona_name or
                        existing_player["status"] != new_player.status
                )

                if needs_update:
                    # Обновляем только разрешенные поля
                    self.data[player_index]["persona_name"] = new_player.persona_name
                    self.data[player_index]["status"] = new_player.status
                    self.data[player_index]["last_upd"] = current_time
                    has_changes = True
                    print(f"Обновлен игрок: {new_player.steam_id}")

        # Обновляем общее время последнего обновления если были изменения
        if has_changes:
            self._last_updated = current_time
            self.save()
            print(f"Данные успешно сохранены. Обновлено: {datetime.fromtimestamp(current_time)}")
        else:
            print("Изменений не обнаружено")

    def update_list(self, reqest: list[PlayerAnalysisForJson]):
        self._procces_from_request(reqest)

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
