# schemas/dictionary.py
from typing import Optional

from pydantic import Field

from steam_analysis.core.schemas.base import (SteamEntityMixin, StatsMixin, AchievMixin, 
                                              AchievPercentMixin, BaseSchema, ReviewMixin, NewMixin)


class CategoryBase(SteamEntityMixin):
    """Базовая схема категории"""
    pass

class CategoryCreate(CategoryBase):
    """Схема для создания категории"""
    pass  # Steam API использует 'id'

class CategoryUpdate(BaseSchema):
    """Схема для обновления категории"""
    description: Optional[str] = Field(None, max_length=1000)

class CategoryResponse(CategoryBase):
    """Схема ответа для категории"""
    pass


class GenreBase(SteamEntityMixin):
    pass

class GenreCreate(GenreBase):
    pass

class GenreUpdate(BaseSchema):
    description: Optional[str] = None

class GenreResponse(GenreBase):
    pass


class PlatformBase(BaseSchema):
    description: Optional[str] = Field(None, max_length=1000)
    pass

class PlatformCreate(PlatformBase):
    pass


class PlatformUpdate(BaseSchema):
    pass



class PlatformResponse(PlatformBase):
    pass


class StatsBase(StatsMixin):
    pass

class StatsCreate(StatsBase):
    pass

class StatsUpdate(BaseSchema):
    description: Optional[str] = None

class StatsResponse(StatsBase):
    pass


class AchievBase(AchievMixin):
    pass

class AchievCreate(AchievBase):
    pass

class AchievUpdate(BaseSchema):
    description: Optional[str] = None

class AchievResponse(AchievBase):
    pass


class AchievPercentBase(AchievPercentMixin):
    pass

class AchievPercentCreate(AchievPercentBase):
    pass

class AchievPercentUpdate(BaseSchema):
    description: Optional[str] = None

class AchievPercentResponse(AchievPercentBase):
    pass


class ReviewBase(ReviewMixin):
    pass

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseSchema):
    description: Optional[str] = None

class ReviewResponse(ReviewBase):
    pass


class NewBase(NewMixin):
    pass

class NewCreate(NewBase):
    pass

class NewUpdate(BaseSchema):
    description: Optional[str] = None

class NewResponse(NewBase):
    pass



class TypeBase(BaseSchema):
    description: Optional[str] = Field(None, max_length=1000)
    pass


class TypeCreate(PlatformBase):
    pass


class TypeUpdate(BaseSchema):
    pass


class TypeResponse(PlatformBase):
    pass
