from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema, TimestampMixin, IDMixin
from .dictionaries import CategoryResponse, GenreResponse, PlatformResponse, TypeBase, TypeCreate


@dataclass
class GameShortInfo:
    app_id: int
    name: str


@dataclass
class GameCategory:
    category_id: int
    name: str


class GameBase(BaseSchema):
    """Базовые поля игры (редко меняются)"""
    app_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=255)
    is_free: bool = False
    release_date: Optional[datetime] = None
    coming_soon: bool = False
    controller_support: Optional[str] = None
    # developers: List[str] ??
    # publishers: List[str] ??


class GameFromHttp(GameBase):
    type: TypeBase


class GameCreate(GameBase):
    """DTO для создания игры"""
    type_id: int


class GameUpdate(BaseSchema):
    """DTO для обновления игры (только изменяемые поля)"""
    is_free: Optional[bool] = None
    coming_soon: Optional[bool] = None
    controller_support: Optional[str] = None


class GameResponse(GameBase, TimestampMixin, IDMixin):
    """Схема ответа для игры"""
    pass


class GameWithRelationsResponse(GameResponse):
    """Игра со связанными данными"""
    genres: List[GenreResponse] = Field(default_factory=list)
    categories: List[CategoryResponse] = Field(default_factory=list)
    platforms: List[PlatformResponse] = Field(default_factory=list)
