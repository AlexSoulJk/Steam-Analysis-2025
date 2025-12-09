from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BaseSchema(BaseModel):
    """Базовая схема с общими настройками"""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class TimestampMixin(BaseSchema):
    """Миксин для временных меток"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IDMixin(BaseSchema):
    """Миксин для ID"""
    id: Optional[int] = Field(None, description="ID записи")

class SteamEntityMixin(BaseSchema):
    """Миксин для Steam сущностей"""
    steam_id: int = Field(..., description="ID в Steam API", alias="id")
    description: Optional[str] = Field(None, max_length=1000)

    model_config = ConfigDict(
        populate_by_name=True,  # Разрешить использовать оба имени
        alias_generator=None
    )


class StatsMixin(BaseSchema):
    """Миксин для Stats&Achiev"""
    name: str = Field(..., description="Название статистики", alias="name")
    default_value: int = Field(..., description="Значение по умолчанию", alias="defaultvalue")
    display_name: str = Field(..., description="Отображаемое имя", alias="displayName")

class AchievMixin(BaseSchema):
    """Миксин для Stats&Achiev"""
    name: str = Field(..., description="Название статистики", alias="name")
    defaultvalue: int = Field(..., description="Значение по умолчанию", alias="defaultvalue")
    displayName: str = Field(..., description="Отображаемое имя", alias="displayName")
    hidden: int = Field(..., description="Скрыта ли статистика", alias="hidden")
    # icon: str = Field(..., description="URL иконки", alias="icon")
    # icon_gray: str = Field(..., description="URL серой иконки", alias="icongray")

class AchievPercentMixin(BaseSchema):
    """Миксин для Achiev"""
    percent: float = Field(..., description="Процент игроков с достижением", ge=0, le=100)


class ReviewAuthorMixin(BaseSchema):
    """Схема для автора отзыва"""
    steam_id: str = Field(..., alias="steamid")
    # num_games_owned: int = Field(..., ge=0)
    # num_reviews: int = Field(..., ge=0)
    # playtime_forever: int = Field(..., ge=0)
    # playtime_last_two_weeks: int = Field(..., ge=0)
    # playtime_at_review: int = Field(..., ge=0)
    # last_played: int = Field(..., ge=0)

class ReviewMixin(BaseSchema):
    """Миксин для отзыва"""
    recommendation_id: str = Field(..., alias="recommendationid")
    author: ReviewAuthorMixin
    language: str
    review: str
    timestamp_created: int = Field(..., ge=0)
    timestamp_updated: int = Field(..., ge=0)
    voted_up: bool
    votes_up: int = Field(..., ge=0)
    votes_funny: int = Field(..., ge=0)
    weighted_vote_score: float = Field(..., ge=0, le=1)
    comment_count: int = Field(..., ge=0)
    # steam_purchase: bool
    received_for_free: bool
    written_during_early_access: bool
    # primarily_steam_deck: bool


class NewMixin(BaseSchema):
    """Миксин для новости по игре"""
    gid: str = Field(..., description="ID новости")
    title: str = Field(..., description="Заголовок новости")
    # url: str = Field(..., description="URL новости")
    # is_external_url: bool = Field(..., description="Внешняя ссылка")
    author: str = Field(..., description="Автор новости")
    contents: str = Field(..., description="Содержание новости (HTML)")
    feedlabel: str = Field(..., description="Метка фида")
    date: int = Field(..., ge=0, description="Дата публикации (timestamp)")
    feedname: str = Field(..., description="Название фида")
    feed_type: int = Field(..., description="Тип фида")
