from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import IntEnum

from pydantic import Field, field_validator

from steam_analysis.core.schemas.base import BaseSchema


class RatingCore(BaseSchema):
    """Базовая модель времени игры"""
    rating: int
    req_age: int
    banned: bool


class RatingBase(RatingCore):
    """Базовая модель времени игры"""
    game_id: int
    rating_name_id: int


class RatingCreate(RatingBase):
    """DTO для создания времени игры"""
    pass


class RatingHttp(RatingCore):
    """Базовая модель времени игры"""
    rating_name: str


class RatingNameBase(BaseSchema):
    """Базовая модель времени игры"""
    description: str


class RatingNameCreate(RatingNameBase):
    """DTO для создания времени игры"""
    pass
