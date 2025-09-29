import json
from pathlib import Path
from steam_analysis.resourcemanager.resources.base import Resource
from steam_analysis.resourcemanager.resources.codes import ResourceCodes


class GameCategory(Resource):
    """Ресурс для хранения полного каталога игр"""

    def __init__(self, resource_base_path: Path):
        super().__init__(
            ResourceCodes.GAME_CATEGORIES,
            resource_base_path=resource_base_path,
            ttl_hours=168  # 1 неделя
        )

    def load(self) -> bool:
        try:
            if not self.file_path.exists():
                return False

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.update(data.get("data"), data.get("last_upd"))
                return True

        except Exception as e:
            # logger.error(f"Failed to load game catalog: {e}")
            return False

    def save(self) -> bool:
        if self._data is None:
            return False

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({"last_upd": self._last_updated, "data": self._data}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            # logger.error(f"Failed to save game catalog: {e}")
            return False