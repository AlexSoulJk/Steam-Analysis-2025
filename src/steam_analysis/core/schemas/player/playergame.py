from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import IntEnum

from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema, TimestampMixin, IDMixin


class PlayerGameRelation(BaseSchema):
    steam_id: str
    app_id: str


class PlaytimeCore(BaseSchema):
    """Базовая модель времени игры"""
    playtime_forever: Optional[int] = Field(None, ge=0)
    playtime_2weeks: Optional[int] = Field(None, ge=0)
    last_played: Optional[datetime] = Field(None)


class PlaytimeBase(PlaytimeCore):
    """Базовая модель времени игры"""
    user_id: int
    game_id: int


class PlaytimeCreate(PlaytimeBase):
    """DTO для создания времени игры"""
    pass


class PlaytimeHttp(PlayerGameRelation, PlaytimeCore):
    """Базовая модель времени игры"""
    steam_id: str
    app_id: str


class OwnershipBase(BaseSchema):
    """Базовая модель владения игрой"""
    user_id: int
    game_id: int
    owned: bool = Field(True)


class OwnershipCreate(OwnershipBase):
    """DTO для создания владения игрой"""
    pass


class OwnershipHttp(PlayerGameRelation):
    """DTO для создания владения игрой"""
    pass


class AchievementCore(BaseSchema):
    """Базовая модель достижения"""
    achieved: bool = Field(False)
    unlock_time: Optional[datetime] = Field(None)
    unlock_timestamp: Optional[int] = Field(None, ge=0)


class AchievementBase(AchievementCore):
    """Базовая модель достижения"""
    user_id: int
    game_id: int
    achievement_id: int  #???


class AchievementCreate(AchievementBase):
    """DTO для создания достижения"""
    pass


class AchievementHttp(PlayerGameRelation, AchievementCore):
    """Базовая модель достижения"""
    pass


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


class ReviewHttp(ReviewCore):
    """DTO для создания отзыва"""
    app_id: str


class LogoffHistoryBase(BaseSchema):
    """Базовая модель истории выходов"""
    user_id: int
    last_logoff: datetime


class LogoffHistoryCreate(LogoffHistoryBase):
    """DTO для создания записи о выходе"""
    pass


class LogoffHistoryHttp(BaseSchema):
    """DTO для создания записи о выходе"""
    steam_id: str
    last_logoff: datetime
