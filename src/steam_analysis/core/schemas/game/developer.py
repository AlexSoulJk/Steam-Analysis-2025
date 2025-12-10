from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import IntEnum

from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema


class DeveloperBase(BaseSchema):
    """Базовая модель разработчика"""
    name: str
    description: Optional[str]
    website: Optional[str]


class DeveloperCreate(DeveloperBase):
    """DTO для создания времени игры"""
    pass


class PublisherBase(BaseSchema):
    """Базовая модель разработчика"""
    name: str
    description: Optional[str]
    website: Optional[str]


class PublisherCreate(PublisherBase):
    """DTO для создания времени игры"""
    pass


class GameDeveloperBase(BaseSchema):
    """Базовая схема связи игры и разработчика"""
    game_id: int
    developer_id: int


class GameDeveloperCreate(GameDeveloperBase):
    """Схема для создания связи игры и разработчика"""
    pass


class GamePublisherBase(BaseSchema):
    """Базовая схема связи игры и разработчика"""
    game_id: int
    publisher_id: int


class GamePublisherCreate(GamePublisherBase):
    """Схема для создания связи игры и разработчика"""
    pass
