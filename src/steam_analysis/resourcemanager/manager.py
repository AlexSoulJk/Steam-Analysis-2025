import os
from pathlib import Path
from typing import Dict, Any, Optional, Type
from .resources.base import Resource
from .resources.codes import ResourceCodes
from .resources.game_list import GameList
import logging

logger = logging.getLogger(__name__)
RESOURCE_DATA_DIR_NAME = "resources_data"


class ResourceManager:
    """Singleton менеджер ресурсов"""

    _instance = None
    _resources: Dict[ResourceCodes, Resource] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_resources()
        return cls._instance

    @property
    def resource_dir_path(self) -> Path:
        """Путь к директории ресурсов относительно корня проекта"""
        current_file = Path(__file__)
        # Поднимаемся на 4 уровня:
        # .../src/steam_analysis/resourcemanager/manager.py → project_root
        project_root = current_file.parent.parent.parent.parent
        return project_root / RESOURCE_DATA_DIR_NAME

    def _initialize_resources(self):
        """Инициализировать все ресурсы"""
        resource_path = self.resource_dir_path
        logger.info(f"Initializing resources in: {resource_path}")

        self._register_resource(GameList(resource_path))

    def _register_resource(self, resource: Resource):
        """Зарегистрировать ресурс"""
        self._resources[resource.name] = resource
        logger.info(f"Registered resource: {resource.name.value}")

    def get_resource(self, resource_name: ResourceCodes) -> Optional[Resource]:
        """Получить ресурс по имени"""
        return self._resources.get(resource_name)

    def is_resource_expired(self, resource_name: ResourceCodes) -> bool:
        """Проверить, устарел ли ресурс"""
        resource = self.get_resource(resource_name)
        return resource.is_expired if resource else True

    def load_resource(self, resource_name: ResourceCodes) -> bool:
        """Загрузить ресурс из хранилища"""
        resource = self.get_resource(resource_name)
        if not resource:
            logger.error(f"Resource not found: {resource_name.value}")
            return False
        return resource.load()

    def save_resource(self, resource_name: ResourceCodes) -> bool:
        """Сохранить ресурс в хранилище"""
        resource = self.get_resource(resource_name)
        if not resource:
            return False
        return resource.save()

    def update_resource(self, resource_name: ResourceCodes, data: Any) -> bool:
        """Обновить данные ресурса"""
        resource = self.get_resource(resource_name)
        if not resource:
            return False

        resource.update(data)
        return self.save_resource(resource_name)

    def get_resource_data(self, resource_name: ResourceCodes) -> Optional[Any]:
        """Получить данные ресурса"""
        resource = self.get_resource(resource_name)
        return resource.data if resource else None

resource_manager = ResourceManager()