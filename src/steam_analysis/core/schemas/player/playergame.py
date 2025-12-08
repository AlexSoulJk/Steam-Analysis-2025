from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import IntEnum

from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema, TimestampMixin, IDMixin


class PlaytimeBase(BaseSchema):
    """Базовая модель времени игры"""
    playtime_forever: Optional[int] = Field(None, ge=0)
    playtime_2weeks: Optional[int] = Field(None, ge=0)
    last_played: Optional[datetime] = Field(None)


class OwnershipBase(BaseSchema):
    """Базовая модель владения игрой как переделать?"""
    owned: bool = Field(True)
    ownership_date: Optional[datetime] = Field(None)


class AchievementBase(BaseSchema):
    """Базовая модель достижения"""
    achieved: bool = Field(False)
    unlock_time: Optional[datetime] = Field(None)
    unlock_timestamp: Optional[int] = Field(None, ge=0)


class ReviewCore(BaseSchema):
    """Базовая модель отзыва"""
    steam_id: str = Field(..., max_length=20)
    language: Optional[str] = Field(None, max_length=20)
    review: Optional[str] = Field(None)
    voted_up: Optional[bool] = Field(None)
    votes_up: int = Field(0, ge=0)
    votes_funny: int = Field(0, ge=0)
    weighted_vote_score: Optional[float] = Field(None)
    timestamp_created: Optional[int] = Field(None)
    timestamp_updated: Optional[int] = Field(None)
    comment_count: int = Field(0, ge=0)
    steam_purchase: bool = Field(False)
    received_for_free: bool = Field(False)
    written_during_early_access: bool = Field(False)
    primarily_steam_deck: bool = Field(False)


class ReviewBase(ReviewCore):
    """Базовая модель отзыва"""
    game_id: int
    user_id: Optional[int] = Field(None)
    recommendation_id: str = Field(..., max_length=100)


class ReviewCreate(ReviewBase):
    """DTO для создания отзыва"""
    pass

