import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, List
import time
import logging

from steam_analysis.resourcemanager.resources.codes import ResourceCodes

logger = logging.getLogger(__name__)


class Resource(ABC):
    """Абстрактный базовый класс для всех ресурсов"""
    # TODO: Вопрос, кто ответственен за то, чтобы в случае устаревания ресурса выдавать None?
    # Стоит ли установить проверку на is_expired у ресурса сразу в проперти?
    def __init__(self,
                 name: ResourceCodes,  # Теперь типизировано
                 resource_base_path: Path,
                 ttl_hours: int = 24,
                 is_need_for_expired_checking: bool = False):
        self.name: ResourceCodes = name
        self.ttl_hours = ttl_hours
        self._data: Optional[List] = None
        self._last_updated = 0
        self._resource_base_path = resource_base_path
        self.file_extension = "json"
        self._is_loaded = False
        self._ensure_resources_dir()
        self._init_source()
        self._is_need_for_expired_checking = is_need_for_expired_checking

    def _init_source(self):
        tmp = self.load()
        if not tmp:
            self._is_loaded = False
            logger.debug("There was no resource {} yet...".format(self.name))

    @property
    def is_expired(self) -> bool:
        """Проверить, устарели ли данные"""
        status = self._last_updated == 0 or (time.time() - self._last_updated) > (self.ttl_hours * 3600)
        if status and self._is_loaded and self._is_need_for_expired_checking:
            self.clear()
        return status and self._is_need_for_expired_checking


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
    def data(self) -> Optional[List]:
        """Получить данные ресурса"""
        return None if self.is_expired else self._data

    def update(self, data: Any, time: time.time):
        """Обновить данные ресурса"""
        self._data = data
        self._last_updated = time
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

    def clear(self):
        del self._data
        self._data = None
        self._is_loaded = False

