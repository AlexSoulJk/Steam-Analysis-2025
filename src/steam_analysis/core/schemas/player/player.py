from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import IntEnum, Enum

from pydantic import Field

from steam_analysis.core.schemas.base import BaseSchema
from .playergame import AchievementBase, OwnershipBase, ReviewBase, PlaytimeBase


class CommunityVisibilityState(IntEnum):
    PRIVATE = 1
    FRIENDS_ONLY = 2
    PUBLIC = 3


@dataclass
class PlayerShortInfo:
    steam_id: str
    persona_name: Optional[str] = None


class ListPlayerShortInfo(BaseSchema):
    users: List[PlayerShortInfo]


class PlayerBase(BaseSchema):
    """Базовые поля пользователя (редко меняются)"""
    steam_id: str = Field(..., min_length=17, max_length=17)
    persona_name: Optional[str] = Field(None, max_length=255)
    profile_url: Optional[str] = Field(None, max_length=500)
    time_created: Optional[datetime] = None
    community_visibility_state: Optional[CommunityVisibilityState] = None
    steam_level: Optional[int] = Field(None, ge=0)
    loccountrycode: Optional[str] = None
    locstatecode: Optional[str] = None
    loccityid: Optional[int] = None


class SteamUserDynamic(BaseSchema):
    """Данные, которые нужно обновлять"""
    last_logoff: Optional[datetime] = None


class PlayerFromHttp(PlayerBase):
    """Игрок с данными из Steam API"""
    last_logoff: Optional[datetime] = None


class PlayerCreate(PlayerBase):
    """DTO для создания игрока в БД"""
    pass


class PlayerUpdate(BaseSchema):
    """DTO для обновления игрока"""
    persona_name: Optional[str] = Field(None, max_length=255)
    profile_url: Optional[str] = Field(None, max_length=500)
    last_logoff: Optional[datetime] = None
    community_visibility_state: Optional[CommunityVisibilityState] = None
    steam_level: Optional[int] = Field(None, ge=0)


class PlayerResponse(PlayerBase):
    """Базовый ответ с ID БД"""
    id: int
    last_logoff: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FriendStatus(str, Enum):
    VALID = 'valid'
    INVALID = 'invalid'
    PENDING = 'pending'


class FriendBase(BaseSchema):
    """Базовая схема для друга"""
    user_id: int
    friend_id: Optional[int] = None
    user_steamid: Optional[str] = None
    friend_steamid: Optional[str] = None
    status: FriendStatus = Field(default=FriendStatus.VALID)


class FriendCreate(FriendBase):
    """DTO для создания связи дружбы"""
    pass


class FriendResponse(FriendBase):
    """DTO для ответа с данными друга"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PlayerWithFriends(PlayerResponse):
    """Игрок с друзьями"""
    friends: List[FriendResponse] = []
    friends_count: int = 0


class PlayerWithPlaytime(PlayerResponse):
    """Игрок с информацией о времени игры"""
    playtime: List[PlaytimeBase] = []
    total_playtime: Optional[int] = Field(None, ge=0)
    games_count: int = 0


class PlayerWithGames(PlayerResponse):
    """Игрок с библиотекой игр"""
    owned_games: List[OwnershipBase] = []
    playtime_stats: List[PlaytimeBase] = []
    total_games_count: int = 0


class PlayerWithAchievements(PlayerResponse):
    """Игрок с достижениями"""
    achievements: List[AchievementBase] = []
    total_achievements: int = 0
    unlocked_achievements: int = 0
    completion_rate: Optional[float] = Field(None, ge=0, le=100)  # в процентах


class PlayerWithReviews(PlayerResponse):
    """Игрок с отзывами - как их можно получать (имеется модель, но как она заполняется)"""
    reviews: List[ReviewBase] = []
    reviews_count: int = 0
    positive_reviews: int = 0
    negative_reviews: int = 0


class PlayerFullProfile(PlayerResponse):
    """Полный профиль игрока со всей информацией"""
    playtime: List[PlaytimeBase] = []
    owned_games: List[OwnershipBase] = []
    achievements: List[AchievementBase] = []
    # reviews: List[ReviewBase] = []
    steam_level: Optional[int] = None
    # friends: Optional[List[str]] = None
    loccountrycode: Optional[str] = None
    locstatecode: Optional[str] = None
    loccityid: Optional[int] = None


class PlayerFullFromHttp(PlayerFromHttp):
    owned_games: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # playtime: List[PlaytimeBase] = []
    # owned_games: List[OwnershipBase] = []
    # achievements: List[AchievementBase] = []
    # reviews: List[ReviewBase] = []

