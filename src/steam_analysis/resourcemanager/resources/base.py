import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import time
import logging

from steam_analysis.resourcemanager.resources.codes import ResourceCodes

logger = logging.getLogger(__name__)


class Resource(ABC):
    """Абстрактный базовый класс для всех ресурсов"""

    def __init__(self,
                 name: ResourceCodes,  # Теперь типизировано
                 resource_base_path: Path,
                 ttl_hours: int = 24):
        self.name: ResourceCodes = name
        self.ttl_hours = ttl_hours
        self._data = None
        self._last_updated = 0
        self._resource_base_path = resource_base_path
        self.file_extension = "json"
        self._ensure_resources_dir()

    @property
    def is_expired(self) -> bool:
        """Проверить, устарели ли данные"""
        if self._last_updated == 0:
            return True
        return (time.time() - self._last_updated) > (self.ttl_hours * 3600)

    @property
    def resource_file_dir(self) -> Path:
        """Директория для файла ресурса"""
        return self._resource_base_path / self.name.value.lower()

    @property
    def file_path(self) -> Path:
        """Полный путь к файлу ресурса"""
        return self.resource_file_dir / f"{self.name.value}.{self.file_extension}"

    def _ensure_resources_dir(self):
        """Создать директорию ресурсов если не существует"""
        os.makedirs(self.resource_file_dir, exist_ok=True)

    @property
    def data(self) -> Optional[Any]:
        """Получить данные ресурса"""
        return self._data

    def update(self, data: Any):
        """Обновить данные ресурса"""
        self._data = data
        self._last_updated = time.time()
        items_count = len(data) if hasattr(data, '__len__') else '?'
        logger.info(f"Resource '{self.name.value}' updated with {items_count} items")

    @abstractmethod
    def load(self) -> bool:
        """Загрузить данные из постоянного хранилища"""
        pass

    @abstractmethod
    def save(self) -> bool:
        """Сохранить данные в постоянное хранилище"""
        pass
