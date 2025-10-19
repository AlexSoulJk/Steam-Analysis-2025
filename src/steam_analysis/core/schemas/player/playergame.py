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
    """Базовая модель владения игрой"""
    owned: bool = Field(True)
    ownership_date: Optional[datetime] = Field(None)


class AchievementBase(BaseSchema):
    """Базовая модель достижения"""
    achieved: bool = Field(False)
    unlock_time: Optional[datetime] = Field(None)
    unlock_timestamp: Optional[int] = Field(None, ge=0)


class ReviewBase(BaseSchema):
    """Базовая модель отзыва"""
    language: Optional[str] = Field(None, max_length=20)
    review: Optional[str] = Field(None)
    voted_up: Optional[bool] = Field(None)
    votes_up: int = Field(0, ge=0)
    votes_funny: int = Field(0, ge=0)
    weighted_vote_score: Optional[float] = Field(None)
    timestamp_created: Optional[int] = Field(None)
    timestamp_updated: Optional[int] = Field(None)
    written_during_early_access: bool = Field(False)
